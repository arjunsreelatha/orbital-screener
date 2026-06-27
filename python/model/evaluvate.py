import sys
import torch
import numpy as np
import pickle
from pathlib import Path
from torch.utils.data import DataLoader
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

sys.path.append(str(Path(__file__).resolve().parents[1]))

from dataset import load_dataset, normalize_sequences, collate_fn, ConjunctionDataset
from model import ConjunctionLSTM

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH     = PROJECT_ROOT / "data" / "conjunctions" / "dataset.csv"
MODEL_PATH   = PROJECT_ROOT / "data" / "model.pt"
SCALER_PATH  = PROJECT_ROOT / "data" / "scaler.pkl"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def evaluate():
    sequences, labels = load_dataset(CSV_PATH)

    idx = list(range(len(sequences)))
    train_idx, temp_idx = train_test_split(idx, test_size=0.3, random_state=42, stratify=labels)
    val_idx, test_idx   = train_test_split(temp_idx, test_size=0.5, random_state=42,
                                            stratify=[labels[i] for i in temp_idx])

    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    test_seqs   = [sequences[i] for i in test_idx]
    test_seqs, _ = normalize_sequences(test_seqs, scaler)
    test_labels  = [labels[i] for i in test_idx]

    test_ds     = ConjunctionDataset(test_seqs, test_labels)
    test_loader = DataLoader(test_ds, batch_size=64, shuffle=False, collate_fn=collate_fn)

    model = ConjunctionLSTM().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    all_probs  = []
    all_preds  = []
    all_labels = []

    with torch.no_grad():
        for padded, lengths, batch_labels in test_loader:
            padded  = padded.to(DEVICE)
            lengths = lengths.to(DEVICE)
            logits  = model(padded, lengths)
            probs   = torch.softmax(logits, dim=1).cpu().numpy()
            preds   = np.argmax(probs, axis=1)
            all_probs.append(probs)
            all_preds.extend(preds)
            all_labels.extend(batch_labels.numpy())

    all_probs  = np.vstack(all_probs)
    all_preds  = np.array(all_preds)
    all_labels = np.array(all_labels)

    print("\n--- Evaluation Results ---")
    print(f"Test samples: {len(all_labels)}")

    # confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    print(f"\nConfusion Matrix (rows=actual, cols=predicted):")
    print(f"         LOW  MED  HIGH")
    for i, row in enumerate(cm):
        name = ["LOW ", "MED ", "HIGH"][i]
        print(f"  {name}  {row}")

    # F1 macro
    f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
    print(f"\nF1 Macro: {f1:.4f}")

    # ROC-AUC
    try:
        auc = roc_auc_score(all_labels, all_probs, multi_class="ovr", average="macro")
        print(f"ROC-AUC (macro OvR): {auc:.4f}")
    except Exception as e:
        print(f"ROC-AUC error: {e}")

    # heuristic baseline — rank by miss_distance_km only
    print("\n--- Heuristic Baseline (miss distance only) ---")
    import pandas as pd
    df = pd.read_csv(CSV_PATH)
    df["pair_key"] = [tuple(sorted([a, b])) for a, b in zip(df["object1_name"], df["object2_name"])]
    df = df.sort_values(["pair_key", "tca_unix"])
    baseline_labels = []
    baseline_scores = []
    for pair_key, group in df.groupby("pair_key"):
        if len(group) < 2:
            continue
        from dataset import LABEL_MAP
        label_ints = [LABEL_MAP[l] for l in group["risk_label"]]
        label = max(label_ints)
        # heuristic score = 1 / min miss distance (closer = higher risk)
        score = 1.0 / group["miss_distance_km"].min()
        baseline_labels.append(label)
        baseline_scores.append(score)

    baseline_labels = np.array(baseline_labels)
    baseline_scores = np.array(baseline_scores)
    # convert to prob-like for AUC
    from sklearn.preprocessing import minmax_scale
    baseline_probs = np.zeros((len(baseline_scores), 3))
    baseline_probs[:, 2] = minmax_scale(baseline_scores)
    baseline_probs[:, 0] = 1 - baseline_probs[:, 2]
    try:
        baseline_auc = roc_auc_score(baseline_labels, baseline_probs, multi_class="ovr", average="macro")
        print(f"Baseline ROC-AUC: {baseline_auc:.4f}")
    except Exception as e:
        print(f"Baseline AUC error: {e}")

if __name__ == "__main__":
    evaluate()