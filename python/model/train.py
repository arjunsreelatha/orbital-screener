import sys
import torch
import numpy as np
from torch import nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from pathlib import Path
import pickle

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataset import load_dataset, normalize_sequences, collate_fn, ConjunctionDataset
from model import ConjunctionLSTM

# paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH     = PROJECT_ROOT / "data" / "conjunctions" / "dataset.csv"
MODEL_PATH   = PROJECT_ROOT / "data" / "model.pt"
SCALER_PATH  = PROJECT_ROOT / "data" / "scaler.pkl"

# hyperparameters
BATCH_SIZE  = 64
MAX_EPOCHS  = 50
PATIENCE    = 10
LR          = 1e-3
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train():
    print(f"Using device: {DEVICE}")

    # load data
    sequences, labels = load_dataset(CSV_PATH)

    # train/val/test split by sequence (not snapshot)
    idx = list(range(len(sequences)))
    train_idx, temp_idx = train_test_split(idx, test_size=0.3, random_state=42, stratify=labels)
    val_idx, test_idx   = train_test_split(temp_idx, test_size=0.5, random_state=42,
                                            stratify=[labels[i] for i in temp_idx])

    # normalize — fit on train only
    train_seqs = [sequences[i] for i in train_idx]
    train_seqs, scaler = normalize_sequences(train_seqs)
    val_seqs   = [sequences[i] for i in val_idx]
    val_seqs,  _       = normalize_sequences(val_seqs, scaler)
    test_seqs  = [sequences[i] for i in test_idx]
    test_seqs, _       = normalize_sequences(test_seqs, scaler)

    train_labels = [labels[i] for i in train_idx]
    val_labels   = [labels[i] for i in val_idx]
    test_labels  = [labels[i] for i in test_idx]

    # save scaler
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)

    # datasets
    train_ds = ConjunctionDataset(train_seqs, train_labels)
    val_ds   = ConjunctionDataset(val_seqs,   val_labels)

    # class weights for imbalance
    class_weights = compute_class_weight("balanced", classes=np.array([0,1,2]), y=train_labels)
    class_weights = torch.tensor(class_weights, dtype=torch.float).to(DEVICE)

    # weighted sampler
    sample_weights = [class_weights[l].item() for l in train_labels]
    sampler = WeightedRandomSampler(sample_weights, num_samples=len(train_labels))

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler, collate_fn=collate_fn)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,   collate_fn=collate_fn)

    # model
    model     = ConjunctionLSTM().to(DEVICE)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    # training loop
    best_val_loss = float("inf")
    patience_counter = 0

    for epoch in range(MAX_EPOCHS):
        model.train()
        train_loss = 0.0
        for padded, lengths, batch_labels in train_loader:
            padded       = padded.to(DEVICE)
            lengths      = lengths.to(DEVICE)
            batch_labels = batch_labels.to(DEVICE)

            optimizer.zero_grad()
            logits = model(padded, lengths)
            loss   = criterion(logits, batch_labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for padded, lengths, batch_labels in val_loader:
                padded       = padded.to(DEVICE)
                lengths      = lengths.to(DEVICE)
                batch_labels = batch_labels.to(DEVICE)
                logits       = model(padded, lengths)
                val_loss    += criterion(logits, batch_labels).item()

        train_loss /= len(train_loader)
        val_loss   /= len(val_loader)

        print(f"Epoch {epoch+1}/{MAX_EPOCHS} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss    = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), MODEL_PATH)
            print(f"  → saved best model (val_loss={val_loss:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                print(f"Early stopping at epoch {epoch+1}")
                break

    print("Training complete.")
    print(f"Best val loss: {best_val_loss:.4f}")
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()