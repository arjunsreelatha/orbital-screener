import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import StandardScaler
from collections import Counter

LABEL_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

FEATURE_COLS = [
    
    "relative_velocity_km_s",
    "time_to_tca_hours",
    "miss_distance_delta",
    
]

class ConjunctionDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = sequences
        self.labels    = labels

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        seq   = torch.tensor(self.sequences[idx], dtype=torch.float32)
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return seq, label


def load_dataset(csv_path):
    print("Loading CSV...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows")

    # fast pair key
    df["pair_key"] = [
        tuple(sorted([a, b]))
        for a, b in zip(df["object1_name"], df["object2_name"])
    ]

    # sort by pair and timestamp
    df = df.sort_values(["pair_key", "tca_unix"])

    # group into sequences
    sequences = []
    labels    = []

    for pair_key, group in df.groupby("pair_key"):
        if len(group) < 2:
            continue
        features   = group[FEATURE_COLS].values.astype(np.float32)
        label_ints = [LABEL_MAP[l] for l in group["risk_label"]]
        label      = max(label_ints)
        sequences.append(features)
        labels.append(label)

    print(f"Total sequences: {len(sequences)}")
    label_names = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
    dist = Counter(label_names[l] for l in labels)
    print(f"Sequence label distribution: {dict(dist)}")

    return sequences, labels


def normalize_sequences(sequences, scaler=None):
    all_rows = np.vstack(sequences)
    if scaler is None:
        scaler = StandardScaler()
        scaler.fit(all_rows)
    normalized = [scaler.transform(seq) for seq in sequences]
    return normalized, scaler


def collate_fn(batch):
    sequences, labels = zip(*batch)
    lengths = torch.tensor([len(s) for s in sequences], dtype=torch.long)
    padded  = torch.nn.utils.rnn.pad_sequence(sequences, batch_first=True)
    labels  = torch.stack(labels)
    return padded, lengths, labels
