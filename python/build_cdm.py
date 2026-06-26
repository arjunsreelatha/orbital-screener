import json
import os
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH   = PROJECT_ROOT / "data" / "conjunctions" / "conjunctions.json"
OUTPUT_PATH  = PROJECT_ROOT / "data" / "conjunctions" / "cdm_records.json"

# PINNED THRESHOLDS — do not change after training starts
HIGH_THRESHOLD_KM   = 1.0
MEDIUM_THRESHOLD_KM = 5.0

def estimate_pc(miss_distance_km):
    if miss_distance_km < HIGH_THRESHOLD_KM:
        return 0.8
    elif miss_distance_km < MEDIUM_THRESHOLD_KM:
        return 0.3
    else:
        return 0.05

def assign_label(miss_distance_km):
    if miss_distance_km < HIGH_THRESHOLD_KM:
        return "HIGH"
    elif miss_distance_km < MEDIUM_THRESHOLD_KM:
        return "MEDIUM"
    else:
        return "LOW"

if __name__ == "__main__":
    print("Processing...")
    labels = Counter()
    i = 0

    with open(INPUT_PATH) as fin, open(OUTPUT_PATH, "w") as fout:
        fout.write("[")
        first = True
        for event in json.load(fin):
            dist = event["miss_distance_km"]
            label = assign_label(dist)
            labels[label] += 1
            record = {
                "event_id":                f"evt_{i:06d}",
                "object1_name":            event["object1_name"].strip(),
                "object2_name":            event["object2_name"].strip(),
                "miss_distance_km":        dist,
                "relative_velocity_km_s":  event["relative_velocity_km_s"],
                "tca_unix":                event["tca_unix"],
                "time_to_tca_hours":       24.0,
                "miss_distance_delta":     0.0,
                "pc_estimate":             estimate_pc(dist),
                "risk_label":              label,
            }
            if not first:
                fout.write(",")
            fout.write(json.dumps(record))
            first = False
            i += 1
        fout.write("]")

    print(f"Total: {i}")
    print(f"Distribution: {dict(labels)}")