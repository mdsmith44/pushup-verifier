"""Summarize per-joint confidence and initial top recognition; no retuning."""
import csv
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pushup.engine import Config, Verifier


def read(path):
    with path.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def main():
    config = Config(**json.loads((ROOT/'config/pilot2_frozen.json').read_text()))
    lines = ['# Pilot3 confidence and startup diagnosis', '',
             'Reproduce with `python examples/diagnose_pilot3.py` after diagnostic extraction using `--include-confidence`. These are diagnostic reruns, not a new evaluation. No settings were changed.', '']
    for clip in ('pilot3_full_reps','pilot3_shallow_reps','pilot3_mixed'):
        data = read(ROOT/f'data/observations/{clip}_diagnostic.csv')
        original = read(ROOT/f'data/observations/{clip}.csv')
        assert len(data) == len(original)
        assert all(a[k] == b[k] for a,b in zip(data,original) for k in ('timestamp','elbow_angle','body_angle','confidence')), 'Diagnostic rerun differs from frozen observations'
        counts = Counter()
        failures = []
        model = Verifier(config, 'temporal')
        first_top = None
        early = []
        for row in data:
            t = float(row['timestamp'])
            elbow = float(row['elbow_angle']) if row['elbow_angle'] else None
            body = float(row['body_angle']) if row['body_angle'] else None
            confidence = float(row['confidence'])
            if row['observation_status'] != 'measured':
                counts[row['observation_status']] += 1
                failures.append((t,row['observation_status']))
            elif confidence < config.min_confidence:
                fields = [k for k in row if k.endswith(('_visibility','_presence')) and float(row[k]) < config.min_confidence]
                counts.update(fields)
                failures.append((t,', '.join(f'{k}={float(row[k]):.3f}' for k in fields)))
            model.update(t, elbow, body, confidence)
            if first_top is None and model.phase == 'top':
                first_top = t
            if t <= .5:
                early.append((t, elbow, model.filtered[0] if model.filtered else None))
        result = model.finish()
        expected = json.loads((ROOT/f'results/{clip}_temporal.json').read_text())
        assert result['attempts'] == expected['attempts']
        lines += [f'## {clip}', '', f'Original measurements and replay attempts reproduced exactly ({len(data)} frames). First confirmed top: {first_top} seconds.', '',
                  f'Failure counts by component (a frame may appear in multiple categories): {dict(counts)}.', '',
                  'First 0.5 seconds: time / raw elbow / filtered elbow (degrees):', '',
                  '```text']
        lines += [f'{t:.3f} / {e} / {s}' for t,e,s in early]
        lines += ['```', '', 'Unreliable frame timestamps and causes:', '', '```text']
        lines += [f'{t:.3f}: {reason}' for t,reason in failures]
        lines += ['```', '']
    lines += ['These scores indicate model confidence, not landmark accuracy. A missing/multiple-pose result is distinct from a low score on one joint. Timestamped manual labels are still required to assign misses to particular repetitions.']
    (ROOT/'docs/pilot3-diagnosis.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
