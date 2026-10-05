"""Plot private pilot measurements and trace the actual verifier state.

Run: python examples/inspect_visibility.py (requires matplotlib).
Outputs remain under the ignored results directory.
"""
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pushup.engine import Verifier
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    with (ROOT / 'data/observations/pilot_visibility.csv').open() as f:
        rows = [{k: float(v) if v else None for k, v in r.items()} for r in csv.DictReader(f)]
    with (ROOT / 'data/labels.csv').open(encoding='utf-8-sig') as f:
        labels = [r for r in csv.DictReader(f) if r['clip_id'] == 'pilot_visibility']
    models = {mode: Verifier(mode=mode) for mode in ('immediate', 'temporal')}
    trace, events = [], []
    for r in rows:
        item = dict(r)
        for mode, model in models.items():
            old, count = model.phase, len(model.attempts)
            model.update(r['timestamp'], r['elbow_angle'], r['body_angle'], r['confidence'])
            item[mode + '_phase'] = model.phase
            item[mode + '_elbow'] = model.filtered[0] if model.filtered else None
            if model.phase != old or len(model.attempts) != count:
                events.append(f"{r['timestamp']:.3f}s {mode}: {old} -> {model.phase}; elbow={r['elbow_angle']}; confidence={r['confidence']:.3f}")
        trace.append(item)
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    with (out / 'pilot_visibility_trace.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(trace[0]))
        writer.writeheader()
        writer.writerows(trace)
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True)
    t = [r['timestamp'] for r in trace]
    axes[0].plot(t, [r['elbow_angle'] for r in trace], label='Raw elbow', alpha=.7)
    axes[0].plot(t, [r['temporal_elbow'] for r in trace], label='Temporal elbow')
    for value, name in ((145, 'Top 145'), (130, 'Departure 130'), (90, 'Depth 90')):
        axes[0].axhline(value, linestyle='--', alpha=.5, label=name)
    axes[0].set_ylabel('Elbow angle (degrees)')
    axes[0].legend(loc='lower left', ncol=3, fontsize=8)
    axes[1].plot(t, [r['confidence'] for r in trace], color='purple')
    axes[1].axhline(.6, color='red', linestyle='--', label='Confidence gate 0.6')
    axes[1].set_ylabel('Confidence')
    axes[1].legend()
    phases = {'await_top': 0, 'top': 1, 'attempt': 2}
    for mode in models:
        axes[2].step(t, [phases[r[mode + '_phase']] for r in trace], where='post', label=mode, alpha=.8)
    axes[2].set_yticks([0, 1, 2], ['Await top', 'Top', 'Attempt'])
    axes[2].legend()
    axes[2].set_xlabel('Seconds from video start')
    for label in labels:
        start, end = float(label['start_s']), float(label['end_s'])
        for ax in axes:
            ax.axvspan(start, end, color='grey', alpha=.12)
        axes[0].text((start+end)/2, 178, 'Attempt '+label['attempt_id'], ha='center', fontsize=9)
    for ax in axes:
        ax.grid(alpha=.2)
    fig.suptitle('Visibility pilot: manual attempt windows, measurements, and verifier state')
    fig.tight_layout()
    fig.savefig(out / 'pilot_visibility_diagnostics.png', dpi=150)
    plt.close(fig)
    print('\n'.join(events))
    for start, end in ((3, 4.75), (4.4, 5), (7.5, 9.25), (8.9, 9.438)):
        window = [r for r in trace if start <= r['timestamp'] <= end]
        reliable = [r for r in window if r['confidence'] >= .6 and r['elbow_angle'] is not None and r['body_angle'] is not None]
        print(f'Window {start}-{end}: {len(reliable)}/{len(window)} reliable; max reliable elbow {max((r["elbow_angle"] for r in reliable), default=None)}')
    for mode, model in models.items():
        print(mode, model.finish()['counts'])


if __name__ == '__main__':
    main()
