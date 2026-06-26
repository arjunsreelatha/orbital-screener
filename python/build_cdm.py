python -c "
import json
from collections import Counter
from pathlib import Path

INPUT = Path('data/conjunctions/conjunctions.json')
OUTPUT = Path('data/conjunctions/cdm_records.json')

HIGH = 1.0
MEDIUM = 5.0

def estimate_pc(d):
    if d < HIGH: return 0.8
    elif d < MEDIUM: return 0.3
    else: return 0.05

def assign_label(d):
    if d < HIGH: return 'HIGH'
    elif d < MEDIUM: return 'MEDIUM'
    else: return 'LOW'

print('Processing...')
labels = Counter()
i = 0
with open(INPUT) as fin, open(OUTPUT, 'w') as fout:
    fout.write('[')
    first = True
    for event in json.load(fin):
        dist = event['miss_distance_km']
        label = assign_label(dist)
        labels[label] += 1
        record = {
            'event_id': f'evt_{i:06d}',
            'object1_name': event['object1_name'].strip(),
            'object2_name': event['object2_name'].strip(),
            'miss_distance_km': dist,
            'relative_velocity_km_s': event['relative_velocity_km_s'],
            'tca_unix': event['tca_unix'],
            'time_to_tca_hours': 24.0,
            'miss_distance_delta': 0.0,
            'pc_estimate': estimate_pc(dist),
            'risk_label': label,
        }
        if not first: fout.write(',')
        fout.write(json.dumps(record))
        first = False
        i += 1
    fout.write(']')

print('Total:', i)
print('Distribution:', dict(labels))
"