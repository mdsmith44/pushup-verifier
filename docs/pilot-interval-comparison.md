# Pilot interval comparison

Generated with `python examples/compare_pilot.py` from manual labels and saved replay reports.

Development data only; boundaries are approximate. Greedy one-to-one matching takes the greatest interval intersection-over-union (IoU) first, requiring IoU >= 0.5. An interrupted segment can match but is not an assessable decision. Unmatched does not necessarily mean no movement was detected. Component form labels remain incomplete, so this is not a form-accuracy estimate.

| Clip | Mode | Manual attempts | Matched segments | Matched accepted/rejected decisions | Unmatched manual | Unmatched predictions |
|---|---|---:|---:|---:|---:|---:|
| pilot_full_reps | immediate | 5 | 5 | 5 | 0 | 0 |
| pilot_full_reps | temporal | 5 | 2 | 2 | 3 | 1 |
| pilot_shallow_reps | immediate | 3 | 2 | 2 | 1 | 1 |
| pilot_shallow_reps | temporal | 3 | 1 | 1 | 2 | 1 |
| pilot_visibility | immediate | 4 | 1 | 0 | 3 | 1 |
| pilot_visibility | temporal | 4 | 0 | 0 | 4 | 0 |

## pilot_full_reps: immediate

| Manual attempt | Manual interval (s) | Matched prediction (s) | Status | IoU |
|---|---|---|---|---|
| 1 | 0.50–2.75 | 0.867–2.802 | accepted | 0.818 |
| 2 | 3.00–5.25 | 3.468–5.202 | accepted | 0.771 |
| 3 | 5.75–7.50 | 5.937–7.503 | accepted | 0.892 |
| 4 | 8.00–9.75 | 8.203–9.905 | accepted | 0.812 |
| 5 | 10.00–12.00 | 10.338–12.072 | accepted | 0.802 |

## pilot_full_reps: temporal

| Manual attempt | Manual interval (s) | Matched prediction (s) | Status | IoU |
|---|---|---|---|---|
| 1 | 0.50–2.75 | 1.000–3.002 | accepted | 0.699 |
| 2 | 3.00–5.25 | 3.535–5.470 | accepted | 0.694 |
| 3 | 5.75–7.50 | — | unmatched | — |
| 4 | 8.00–9.75 | — | unmatched | — |
| 5 | 10.00–12.00 | — | unmatched | — |

Unmatched prediction: 6.003–14.873 s, unable_to_assess; best manual IoU 0.225.

## pilot_shallow_reps: immediate

| Manual attempt | Manual interval (s) | Matched prediction (s) | Status | IoU |
|---|---|---|---|---|
| 1 | 1.25–3.00 | — | unmatched | — |
| 2 | 3.75–5.75 | 4.235–5.670 | rejected | 0.717 |
| 3 | 6.50–8.75 | 7.070–8.737 | rejected | 0.741 |

Unmatched prediction: 2.268–3.035 s, rejected; best manual IoU 0.410.

## pilot_shallow_reps: temporal

| Manual attempt | Manual interval (s) | Matched prediction (s) | Status | IoU |
|---|---|---|---|---|
| 1 | 1.25–3.00 | — | unmatched | — |
| 2 | 3.75–5.75 | 4.268–6.003 | rejected | 0.658 |
| 3 | 6.50–8.75 | — | unmatched | — |

Unmatched prediction: 7.137–11.005 s, unable_to_assess; best manual IoU 0.358.

## pilot_visibility: immediate

| Manual attempt | Manual interval (s) | Matched prediction (s) | Status | IoU |
|---|---|---|---|---|
| 1 | 3.00–4.75 | — | unmatched | — |
| 2 | 5.00–7.00 | — | unmatched | — |
| 3 | 7.50–9.25 | 7.670–9.438 | unable_to_assess | 0.815 |
| 4 | 10.25–12.00 | — | unmatched | — |

Unmatched prediction: 3.335–3.502 s, unable_to_assess; best manual IoU 0.095.

## pilot_visibility: temporal

| Manual attempt | Manual interval (s) | Matched prediction (s) | Status | IoU |
|---|---|---|---|---|
| 1 | 3.00–4.75 | — | unmatched | — |
| 2 | 5.00–7.00 | — | unmatched | — |
| 3 | 7.50–9.25 | — | unmatched | — |
| 4 | 10.25–12.00 | — | unmatched | — |
