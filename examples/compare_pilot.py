"""Compare saved pilot reports with manual intervals; run from any directory."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = {
    'pilot_full_reps': ('pilot_right_immediate.json', 'pilot_right_top145.json'),
    'pilot_shallow_reps': ('pilot_shallow_immediate.json', 'pilot_shallow_temporal.json'),
    'pilot_visibility': ('pilot_visibility_immediate.json', 'pilot_visibility_temporal.json'),
}


def overlap(a, b):
    intersection = max(0, min(a['end_s'], b['end_s']) - max(a['start_s'], b['start_s']))
    union = max(a['end_s'], b['end_s']) - min(a['start_s'], b['start_s'])
    return intersection / union


def main():
    with (ROOT / 'data/labels.csv').open(encoding='utf-8-sig', newline='') as stream:
        labels = list(csv.DictReader(stream))
    for row in labels:
        for key in ('start_s', 'end_s'):
            row[key] = float(row[key])
        assert row['end_s'] > row['start_s']
    lines = ['# Pilot interval comparison', '',
             'Generated with `python examples/compare_pilot.py` from manual labels and saved replay reports.', '',
             'Development data only; boundaries are approximate. Greedy one-to-one matching takes the greatest interval intersection-over-union (IoU) first, requiring IoU >= 0.5. An interrupted segment can match but is not an assessable decision. Unmatched does not necessarily mean no movement was detected. Component form labels remain incomplete, so this is not a form-accuracy estimate.', '',
             '| Clip | Mode | Manual attempts | Matched segments | Matched accepted/rejected decisions | Unmatched manual | Unmatched predictions |',
             '|---|---|---:|---:|---:|---:|---:|']
    details = []
    for clip, files in REPORTS.items():
        manual = [r for r in labels if r['clip_id'] == clip]
        for filename in files:
            report = json.loads((ROOT / 'docs/pilot-reports' / filename).read_text(encoding='utf-8-sig'))
            predictions = report['attempts']
            candidates = sorted(((overlap(m, p), i, j) for i, m in enumerate(manual)
                                 for j, p in enumerate(predictions)), reverse=True)
            matches, used = {}, set()
            for score, i, j in candidates:
                if score >= 0.5 and i not in matches and j not in used:
                    matches[i] = (j, score)
                    used.add(j)
            assessed = sum(predictions[j]['status'] in ('accepted', 'rejected') for j, _ in matches.values())
            lines.append(f"| {clip} | {report['mode']} | {len(manual)} | {len(matches)} | {assessed} | {len(manual)-len(matches)} | {len(predictions)-len(used)} |")
            details.extend(['', f"## {clip}: {report['mode']}", '',
                            '| Manual attempt | Manual interval (s) | Matched prediction (s) | Status | IoU |',
                            '|---|---|---|---|---|'])
            for i, m in enumerate(manual):
                prefix = f"| {m['attempt_id']} | {m['start_s']:.2f}–{m['end_s']:.2f} |"
                if i in matches:
                    j, score = matches[i]
                    p = predictions[j]
                    details.append(prefix + f" {p['start_s']:.3f}–{p['end_s']:.3f} | {p['status']} | {score:.3f} |")
                else:
                    details.append(prefix + ' — | unmatched | — |')
            for j, p in enumerate(predictions):
                if j not in used:
                    best = max((overlap(m, p) for m in manual), default=0)
                    details.extend(['', f"Unmatched prediction: {p['start_s']:.3f}–{p['end_s']:.3f} s, {p['status']}; best manual IoU {best:.3f}."])
    output = ROOT / 'docs/pilot-interval-comparison.md'
    output.write_text('\n'.join(lines + details) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
