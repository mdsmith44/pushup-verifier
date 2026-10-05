"""Offline development experiments; does not change the production verifier.

Run from the repository: python examples/pilot_experiments.py
"""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pushup.engine import Config, Verifier


def reliable(row, config):
    return row['elbow_angle'] is not None and row['body_angle'] is not None and row['confidence'] >= config.min_confidence


def replay(rows, config, mode, tolerate=False):
    model = Verifier(config, mode)
    skipped = []
    for i, row in enumerate(rows):
        # Offline lookahead: one bad observation bounded by two valid observations.
        # The entire bracket must span <=75 ms. Never substitute an angle or let
        # temporal persistence/smoothing carry through the unobserved frame.
        isolated = (tolerate and 0 < i < len(rows)-1
                    and not reliable(row, config)
                    and reliable(rows[i-1], config) and reliable(rows[i+1], config)
                    and rows[i+1]['timestamp']-rows[i-1]['timestamp'] <= .075)
        if isolated:
            skipped.append({'start_s': row['timestamp'], 'end_s': rows[i+1]['timestamp']})
            model.holds.clear()
            model.filtered = None
            continue
        model.update(row['timestamp'], row['elbow_angle'], row['body_angle'], row['confidence'])
    report = model.finish()
    report['tolerated_gaps'] = skipped
    report['experiment_note'] = 'Offline single-frame tolerance; accepted decisions spanning tolerated gaps are conditional on unobserved technique. No angles are imputed. Core uncertainty_intervals exclude separately listed tolerated_gaps.'
    for attempt in report['attempts']:
        attempt['contains_tolerated_gap'] = any(g['start_s'] >= attempt['start_s'] and g['start_s'] <= attempt['end_s'] for g in skipped)
    return report


def main():
    clips = {'pilot_full_reps': 'pilot_right.csv', 'pilot_shallow_reps': 'pilot_shallow.csv', 'pilot_visibility': 'pilot_visibility.csv'}
    variants = [('baseline',145,False), ('top140',140,False), ('one_frame',145,True), ('combined',140,True)]
    out = ROOT / 'results/experiments'
    out.mkdir(parents=True, exist_ok=True)
    lines = ['# Pilot threshold and dropout experiments', '',
             'Reproduce: `python examples/pilot_experiments.py`. Requires the private observation CSVs; no model rerun is needed. Defaults and original reports remain unchanged.', '',
             'A/R/U = accepted/rejected/unable to assess tracked segments, not one-to-one manual matches. Single-frame tolerance uses offline lookahead, skips one unreliable observation only when reliable neighbors are at most 75 ms apart, and resets smoothing and persistence. It retains tracking state and previously observed depth/alignment evidence. Longer gaps retain the original reset behavior. No missing angle is fabricated. Tolerated gaps remain recorded separately; any acceptance spanning one is conditional, not verified technique throughout. This is an exploratory policy, not a production change.', '',
             '| Clip | Mode | Variant | A/R/U | Tolerated frames | Accepted spanning gap |',
             '|---|---|---|---|---:|---:|']
    for clip, filename in clips.items():
        with (ROOT / 'data/observations' / filename).open(encoding='utf-8-sig') as f:
            rows = [{k: float(v) if v else None for k, v in r.items()} for r in csv.DictReader(f)]
        for mode in ('immediate','temporal'):
            for name, top, tolerate in variants:
                report = replay(rows, Config(top_angle=top), mode, tolerate)
                (out / f'{clip}_{mode}_{name}.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
                counts = '/'.join(str(report['counts'][k]) for k in ('accepted','rejected','unable_to_assess'))
                conditional = sum(a['status']=='accepted' and a['contains_tolerated_gap'] for a in report['attempts'])
                lines.append(f'| {clip} | {mode} | {name} | {counts} | {len(report["tolerated_gaps"])} | {conditional} |')
    (ROOT / 'docs/pilot-experiments.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
