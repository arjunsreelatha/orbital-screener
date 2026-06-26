import json
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH   = PROJECT_ROOT / "data" / "conjunctions" / "featured_records.json"
OUTPUT_PATH  = PROJECT_ROOT / "data" / "conjunctions" / "dataset.csv"

FIELDS = [
    "event_id",
    "object1_name",
    "object2_name",
    "tca_unix",
    "miss_distance_km",
    "relative_velocity_km_s",
    "time_to_tca_hours",
    "miss_distance_delta",
    "pc_estimate",
    "risk_label",
]

if __name__ == "__main__":
    print("Loading featured records...")
    with open(INPUT_PATH) as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records")

    print("Writing CSV...")
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    print(f"Done. Saved to {OUTPUT_PATH}")

    # print stats
    from collections import Counter
    labels = Counter(r["risk_label"] for r in records)
    print(f"Label distribution: {dict(labels)}")
    print(f"Total pairs: {len(set(tuple(sorted([r['object1_name'], r['object2_name']])) for r in records))}")