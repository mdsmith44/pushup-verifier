"""Exploratory ankle discontinuity guard, not a validated form rule.

Run after extracting pilot_visibility_landmarks.csv with --include-landmarks.
"""
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pushup.engine import Config, Verifier


def discontinuity(previous, current):
    """Translation-invariant rates relative to previous projected leg length."""
    dt = current['timestamp'] - previous['timestamp']
    if not 0 < dt <= .25:
        return None
    vectors = []
    for row in (previous, current):
        values = [row.get(k) for k in ('ankle_x','ankle_y','hip_x','hip_y')]
        if any(v is None for v in values):
            return None
        ax, ay, hx, hy = values
        vectors.append((ax-hx, ay-hy))
    old, new = vectors
    length = math.hypot(*old)
    if length < 1:
        return None
    return (math.dist(old, new)/length/dt,
            abs(math.hypot(*new)-length)/length/dt)


def main():
    with (ROOT/'data/observations/pilot_visibility_landmarks.csv').open() as f:
        rows = [{k: float(v) if v else None for k,v in r.items()} for r in csv.DictReader(f)]
    # Fixed exploratory thresholds: 10% of leg length in ~33 ms.
    flags = []
    models = {m: Verifier(Config(top_angle=140), m) for m in ('immediate','temporal')}
    for i, row in enumerate(rows):
        rate = discontinuity(rows[i-1], row) if i else None
        suspect = rate is not None and max(rate) > 3
        if suspect:
            flags.append(dict(timestamp=row['timestamp'], ankle_relative_speed=rate[0], leg_length_rate=rate[1], confidence=row['confidence'], body_angle=row['body_angle']))
        for model in models.values():
            # Blank evidence triggers uncertainty before alignment evaluation.
            model.update(row['timestamp'], row['elbow_angle'], None if suspect else row['body_angle'], row['confidence'])
    report = {'note':'Experimental 3 leg-lengths/second guard; retains normal confidence gate. No automatic acceptance or coordinate correction. Slow drift and consistently incorrect poses may evade this check.',
              'flags':flags, 'replays':{m:v.finish() for m,v in models.items()}}
    output=ROOT/'results/experiments/ankle_guard.json'
    output.parent.mkdir(exist_ok=True, parents=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Flags near attempt 3:', [r for r in flags if 7.5 <= r['timestamp'] <= 9.5])
    print('All flags:', len(flags))
    for mode, result in report['replays'].items():
        print(mode,result['counts'],result['attempts'])
    print('Frames around alignment failure:')
    for i,row in enumerate(rows):
        if 9.20 <= row['timestamp'] <= 9.44:
            print(row['timestamp'],row['body_angle'],row['confidence'],discontinuity(rows[i-1],row))


if __name__ == '__main__':
    main()
