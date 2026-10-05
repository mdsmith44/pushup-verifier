# Pilot threshold and dropout experiments

Reproduce: `python examples/pilot_experiments.py`. Requires the private observation CSVs; no model rerun is needed. Defaults and original reports remain unchanged.

A/R/U = accepted/rejected/unable to assess tracked segments, not one-to-one manual matches. Single-frame tolerance uses offline lookahead, skips one unreliable observation only when reliable neighbors are at most 75 ms apart, and resets smoothing and persistence. It retains tracking state and previously observed depth/alignment evidence. Longer gaps retain the original reset behavior. No missing angle is fabricated. Tolerated gaps remain recorded separately; any acceptance spanning one is conditional, not verified technique throughout. This is an exploratory policy, not a production change.

| Clip | Mode | Variant | A/R/U | Tolerated frames | Accepted spanning gap |
|---|---|---|---|---:|---:|
| pilot_full_reps | immediate | baseline | 5/0/0 | 0 | 0 |
| pilot_full_reps | immediate | top140 | 5/0/0 | 0 | 0 |
| pilot_full_reps | immediate | one_frame | 5/0/0 | 0 | 0 |
| pilot_full_reps | immediate | combined | 5/0/0 | 0 | 0 |
| pilot_full_reps | temporal | baseline | 2/0/1 | 0 | 0 |
| pilot_full_reps | temporal | top140 | 5/0/0 | 0 | 0 |
| pilot_full_reps | temporal | one_frame | 2/0/1 | 0 | 0 |
| pilot_full_reps | temporal | combined | 5/0/0 | 0 | 0 |
| pilot_shallow_reps | immediate | baseline | 0/3/0 | 0 | 0 |
| pilot_shallow_reps | immediate | top140 | 0/8/0 | 0 | 0 |
| pilot_shallow_reps | immediate | one_frame | 0/3/0 | 0 | 0 |
| pilot_shallow_reps | immediate | combined | 0/8/0 | 0 | 0 |
| pilot_shallow_reps | temporal | baseline | 0/1/1 | 0 | 0 |
| pilot_shallow_reps | temporal | top140 | 0/3/0 | 0 | 0 |
| pilot_shallow_reps | temporal | one_frame | 0/1/1 | 0 | 0 |
| pilot_shallow_reps | temporal | combined | 0/3/0 | 0 | 0 |
| pilot_visibility | immediate | baseline | 0/0/2 | 0 | 0 |
| pilot_visibility | immediate | top140 | 0/1/2 | 0 | 0 |
| pilot_visibility | immediate | one_frame | 0/0/2 | 4 | 0 |
| pilot_visibility | immediate | combined | 0/2/1 | 4 | 0 |
| pilot_visibility | temporal | baseline | 0/0/0 | 0 | 0 |
| pilot_visibility | temporal | top140 | 0/0/1 | 0 | 0 |
| pilot_visibility | temporal | one_frame | 0/0/1 | 4 | 0 |
| pilot_visibility | temporal | combined | 0/1/1 | 4 | 0 |
