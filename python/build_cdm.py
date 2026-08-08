import json
import os
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH   = PROJECT_ROOT / "data" / "conjunctions" / "conjunctions.json"
OUTPUT_PATH  = PROJECT_ROOT / "data" / "conjunctions" / "cdm_records.json"

HIGH_DIST_KM    = 5.0
HIGH_VEL_KM_S   = 3.0
MEDIUM_DIST_KM  = 20.0
MEDIUM_VEL_KM_S = 1.0

def assign_label(miss_distance_km, relative_velocity_km_s):
    if miss_distance_km < HIGH_DIST_KM and relative_velocity_km_s > HIGH_VEL_KM_S:
        return "HIGH"
    elif miss_distance_km < MEDIUM_DIST_KM or relative_velocity_km_s > MEDIUM_VEL_KM_S:
        return "MEDIUM"
    else:
        return "LOW"

def estimate_pc(miss_distance_km, relative_velocity_km_s):
    if miss_distance_km < HIGH_DIST_KM and relative_velocity_km_s > HIGH_VEL_KM_S:
        return 0.8
    elif miss_distance_km < MEDIUM_DIST_KM or relative_velocity_km_s > MEDIUM_VEL_KM_S:
        return 0.3
    else:
        return 0.05

def build_cdm():
    print("Processing...")
    labels = Counter()
    i = 0

    with open(INPUT_PATH) as fin, open(OUTPUT_PATH, "w") as fout:
        fout.write("[")
        first = True
        for event in json.load(fin):
            dist = event["miss_distance_km"]
            vel  = event["relative_velocity_km_s"]
            label = assign_label(dist, vel)
            labels[label] += 1
            record = {
                "event_id":                f"evt_{i:06d}",
                "object1_name":            event["object1_name"].strip(),
                "object2_name":            event["object2_name"].strip(),
                "miss_distance_km":        dist,
                "relative_velocity_km_s":  vel,
                "tca_unix":                event["tca_unix"],
                "time_to_tca_hours":       24.0,
                "miss_distance_delta":     0.0,
                "pc_estimate":             estimate_pc(dist, vel),
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

if __name__ == "__main__":
    build_cdm()