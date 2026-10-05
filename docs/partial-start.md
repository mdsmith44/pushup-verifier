# Experimental partial-start reporting

Add `--partial-start` to replay to observe an initial descent and return without claiming that the starting top was verified. Defaults remain unchanged. It may be combined with `--separate-alignment`.

Before any top or movement-evidence interruption, a filtered elbow decrease of at least 10 degrees from the startup maximum plus the existing departure/persistence condition starts one partial attempt. The 10-degree excursion is an exploratory heuristic, not a calibrated movement classifier. Its recorded start is detection time, not a reconstructed manual start. It cannot establish anatomical correctness or distinguish every unrelated arm movement. Stationary bent arms followed by extension do not satisfy the descent condition. After an interruption this startup policy cannot rearm.

A return is always `unable_to_assess` with `start_observed: false`, regardless of observed depth. `completed: true` means a return to top was observed; `completed_movements` counts only top-anchored completions, while `partial_start_returns` counts these initial returns separately. Incomplete partial attempts have `completed: false`. Reasons retain observed depth/alignment failures without asserting fully verified form.

Reproduce from the repository root:

```bash
python -m pushup.replay data/observations/pilot3_mixed_diagnostic.csv --config config/pilot2_frozen.json --mode temporal --separate-alignment --partial-start --output results/pilot3_mixed_partial_start.json
```

## Pilot3 development results

| Clip | Top-anchored completed movements | Partial-start returns | Interrupted attempts |
|---|---:|---:|---:|
| Full | 5 | 0 | 0 |
| Shallow | 2 | 1 | 0 |
| Mixed | 3 | 1 | 1 |

The shallow initial segment is 0.653–2.053 s; mixed initial segment is 1.935–3.770 s. These extra returns are not accepted repetitions. Manual matching remains pending. The mixed final attempt still loses whole-pose evidence at 15.042 s. These findings are development results on inspected clips, not independent validation. All existing angle, persistence, and confidence thresholds remain fixed.
