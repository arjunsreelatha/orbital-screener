import sys
import torch
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

sys.path.append(str(Path(__file__).resolve().parents[1]))

from model.dataset import FEATURE_COLS, LABEL_MAP, normalize_sequences
from model.model import ConjunctionLSTM

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH     = PROJECT_ROOT / "data" / "conjunctions" / "dataset.csv"
MODEL_PATH   = PROJECT_ROOT / "data" / "model.pt"
SCALER_PATH  = PROJECT_ROOT / "data" / "scaler.pkl"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# global state
model  = None
scaler = None
conjunctions = []

def load_model():
    global model, scaler
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    m = ConjunctionLSTM(input_size=3).to(DEVICE)
    m.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    m.eval()
    model = m
    print(f"Model loaded on {DEVICE}")

def run_inference():
    global conjunctions
    print("Loading dataset...")
    df = pd.read_csv(CSV_PATH)
    df["pair_key"] = [
        tuple(sorted([a, b]))
        for a, b in zip(df["object1_name"], df["object2_name"])
    ]
    df = df.sort_values(["pair_key", "tca_unix"])

    results = []
    FEATURE_COLS_INFERENCE = [
        "relative_velocity_km_s",
        "time_to_tca_hours",
        "miss_distance_delta",
    ]

    for pair_key, group in df.groupby("pair_key"):
        if len(group) < 2:
            continue
        features = group[FEATURE_COLS_INFERENCE].values.astype(np.float32)
        features = scaler.transform(features)
        seq = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(DEVICE)
        lengths = torch.tensor([len(features)], dtype=torch.long).to(DEVICE)

        with torch.no_grad():
            logits = model(seq, lengths)
            probs  = torch.softmax(logits, dim=1).cpu().numpy()[0]

        risk_score = float(probs[2])  # probability of HIGH
        risk_label = ["LOW", "MEDIUM", "HIGH"][int(np.argmax(probs))]

        latest = group.iloc[-1]
        results.append({
            "id":                       f"{pair_key[0]}_vs_{pair_key[1]}",
            "object1_name":             pair_key[0],
            "object2_name":             pair_key[1],
            "miss_distance_km":         float(latest["miss_distance_km"]),
            "relative_velocity_km_s":   float(latest["relative_velocity_km_s"]),
            "risk_label":               risk_label,
            "risk_score":               risk_score,
            "confidence":               float(np.max(probs)),
            "snapshot_count":           len(group),
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    conjunctions = results
    print(f"Inference done. {len(conjunctions)} conjunction pairs.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    run_inference()
    yield

app = FastAPI(title="Orbital Screener API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "device": str(DEVICE), "conjunctions_loaded": len(conjunctions)}

@app.get("/conjunctions")
def get_conjunctions(limit: int = 100):
    return conjunctions[:limit]

@app.get("/conjunctions/{conjunction_id}")
def get_conjunction(conjunction_id: str):
    for c in conjunctions:
        if c["id"] == conjunction_id:
            return c
    raise HTTPException(status_code=404, detail="Conjunction not found")