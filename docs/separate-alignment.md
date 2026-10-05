# Separate movement tracking from alignment assessment

Opt-in development mode: `--separate-alignment` on `pushup.replay`. Defaults and the frozen evaluation reports remain unchanged. Input must have been extracted with `--include-confidence`.

Movement confidence is the minimum visibility/presence across shoulder, elbow, and wrist. Alignment confidence uses shoulder, hip, and ankle. If arm evidence is valid but alignment evidence is missing, movement tracking continues, body filtering and alignment persistence reset, and the attempt retains an alignment-unknown flag. No body angle is fabricated. Missing arm evidence, missing/multiple poses, invalid extraction geometry, and excessive timestamp gaps still interrupt tracking. The initial-top requirement remains unchanged. Extraction still conservatively requires valid geometry for its selected landmarks; this mode does not recover every possible missing-body case.

At return to top, `completed: true` records movement completion independently of the form status. Any alignment gap during the tracked attempt (including departure confirmation) produces `unable_to_assess`, even if another form violation was observed; those violations remain in `reasons`. Such completions are never counted as accepted. Interrupted and end-truncated attempts have `completed: false`. `completed_movements` includes accepted, rejected, and completed-but-unassessable attempts. `uncertainty_intervals` describes movement evidence gaps; `alignment_uncertain_timestamps` separately records frames with usable arm but missing alignment evidence, so an empty interval list does not imply fully assessable form.

Example from the repository root:

```bash
python -m pushup.replay data/observations/pilot3_full_reps_diagnostic.csv --mode temporal --config config/pilot2_frozen.json --separate-alignment --output results/pilot3_full_reps_separate_alignment.json
```

## Pilot3 development comparison

| Clip | Expected movements | Baseline completed decisions | New completed movements | New accepted / rejected / completed-unassessable | New interrupted |
|---|---:|---:|---:|---|---:|
| Full | 5 | 3 | 5 | 3 / 0 / 2 | 0 |
| Shallow | 3 | 2 | 2 | 0 / 2 / 0 | 0 |
| Mixed | 5 | 1 | 3 | 0 / 1 / 2 | 1 |

All thresholds remain fixed. The mixed completed-unassessable attempts also lack the required bottom-angle evidence; no claim of valid form is made. Its final tracked attempt is interrupted by whole-pose loss at 15.042 s. Initial movements in shallow/mixed remain untracked pending a qualifying top. Exact manual interval matching is still pending. This is development on previously inspected clips, not independent validation. Baseline replay outputs must remain identical when the flag is omitted.
