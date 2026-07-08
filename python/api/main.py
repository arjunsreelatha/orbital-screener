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


@app.get("/positions")
def get_positions():
    import json
    conj_path = PROJECT_ROOT / "data" / "conjunctions" / "conjunctions.json"
    with open(conj_path) as f:
        raw = json.load(f)
    
    # collect unique satellites with positions
    seen = set()
    satellites = []
    for event in raw[:5000]:  # limit to first 5000 for speed
        for name_key, pos_key in [("object1_name", "pos1_teme"), ("object2_name", "pos2_teme")]:
            name = event[name_key].strip()
            pos  = event[pos_key]
            if name not in seen:
                seen.add(name)
                x, y, z = pos
                r   = (x**2 + y**2 + z**2) ** 0.5
                lat = __import__('math').degrees(__import__('math').asin(z / r))
                lon = __import__('math').degrees(__import__('math').atan2(y, x))
                alt = r - 6371.0
                satellites.append({
                    "name": name,
                    "lon":  lon,
                    "lat":  lat,
                    "alt":  alt
                })
    return satellites

@app.get("/conjunction_lines")
def get_conjunction_lines():
    import json
    conj_path = PROJECT_ROOT / "data" / "conjunctions" / "conjunctions.json"
    with open(conj_path) as f:
        raw = json.load(f)
    
    import math
    lines = []
    for event in raw[:5000]:
        dist = event["miss_distance_km"]
        vel  = event["relative_velocity_km_s"]
        
        # only return HIGH risk pairs
        if not (dist < 5.0 and vel > 3.0):
            continue
            
        def teme_to_lla(pos):
            x, y, z = pos
            r   = math.sqrt(x**2 + y**2 + z**2)
            lat = math.degrees(math.asin(z / r))
            lon = math.degrees(math.atan2(y, x))
            alt = r - 6371.0
            return lon, lat, alt

        lon1, lat1, alt1 = teme_to_lla(event["pos1_teme"])
        lon2, lat2, alt2 = teme_to_lla(event["pos2_teme"])

        lines.append({
            "object1": event["object1_name"].strip(),
            "object2": event["object2_name"].strip(),
            "miss_distance_km": dist,
            "pos1": {"lon": lon1, "lat": lat1, "alt": alt1},
            "pos2": {"lon": lon2, "lat": lat2, "alt": alt2},
        })

    return lines