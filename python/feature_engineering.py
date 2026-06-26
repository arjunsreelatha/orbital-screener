import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH   = PROJECT_ROOT / "data" / "conjunctions" / "cdm_records.json"
OUTPUT_PATH  = PROJECT_ROOT / "data" / "conjunctions" / "featured_records.json"

def compute_features(records):
    # group events by object pair
    pairs = defaultdict(list)
    for record in records:
        key = tuple(sorted([record["object1_name"], record["object2_name"]]))
        pairs[key].append(record)

    # sort each pair by timestamp and compute delta
    result = []
    for key, events in pairs.items():
        events.sort(key=lambda x: x["tca_unix"])
        for i, event in enumerate(events):
            if i == 0:
                event["miss_distance_delta"] = 0.0
            else:
                event["miss_distance_delta"] = (
                    event["miss_distance_km"] - events[i-1]["miss_distance_km"]
                )
            # time_to_tca_hours: how many hours until end of 7-day window
            start_unix = 1782345600.0  # 2026-06-25 00:00:00 UTC
            end_unix   = start_unix + 7 * 24 * 3600
            event["time_to_tca_hours"] = (end_unix - event["tca_unix"]) / 3600.0
            result.append(event)

    return result

if __name__ == "__main__":
    print("Loading CDM records...")
    with open(INPUT_PATH) as f:
        records = json.load(f)
    print(f"Loaded {len(records)} records")

    print("Computing features...")
    featured = compute_features(records)

    print("Writing...")
    with open(OUTPUT_PATH, "w") as f:
        json.dump(featured, f)

    print(f"Done. {len(featured)} records written to {OUTPUT_PATH}")

    # show a pair with multiple snapshots
    from collections import defaultdict, Counter
    pair_counts = defaultdict(int)
    for r in featured:
        key = tuple(sorted([r["object1_name"], r["object2_name"]]))
        pair_counts[key] += 1
    top_pair = max(pair_counts, key=pair_counts.get)
    print(f"Most common pair: {top_pair[0]} vs {top_pair[1]} — {pair_counts[top_pair]} snapshots")