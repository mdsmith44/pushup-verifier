# Second pilot evaluation

Expected outcomes supplied by the recorder before inspecting model predictions on October 4, 2026:

| Clip | Attempts | Expected accepted | Expected rejected | Manual sequence |
|---|---:|---:|---:|---|
| pilot2_full_reps | 5 | 5 | 0 | full, full, full, full, full |
| pilot2_shallow_reps | 3 | 0 | 3 | shallow, shallow, shallow |
| pilot2_mixed | 5 | 3 | 2 | full, shallow, full, shallow, full |

Use `config/pilot2_frozen.json` with temporal mode. This configuration was chosen using the first pilot set: top 140 degrees, departure 130, depth 90, alignment 160, confidence 0.6, persistence 0.1 seconds, smoothing tau 0.08 seconds, maximum timestamp gap 0.25 seconds. No experimental dropout tolerance or ankle guard. Keep settings fixed across this evaluation and report failures without retuning on these clips.

These are recorder judgments, not independently verified labels. Manual attempt timestamps and separate alignment labels have not yet been supplied. Evaluate overall counts and predicted sequence first; do not equate matching counts with correct one-to-one detection. Do not populate manual intervals from predictions. New clips from the same recorder provide a small follow-up evaluation, not evidence of cross-person generalization.

Right side confirmed by recorder for all clips. Processed with MediaPipe Full and the frozen temporal configuration.

| Clip | Accepted | Rejected | Unable to assess tracked segments | Expected accepted/rejected |
|---|---:|---:|---:|---|
| Full | 1 | 0 | 1 | 5 / 0 |
| Shallow | 0 | 0 | 1 | 0 / 3 |
| Mixed | 0 | 0 | 4 | 3 / 2 |

All six interrupted segments ended because required pose evidence was missing. Frequent brief evidence failures show that the pilot-selected configuration is not robust on this new batch. Zero shallow acceptances is not successful shallow classification: no shallow attempt received a completed decision. Counts of interrupted segments are not counts of actual repetitions. Sequence agreement cannot be assessed from completed predictions here. No thresholds were retuned after these results.

Saved reports are in `pilot2-reports/`. Private observations include landmark coordinates for follow-up diagnostics. The next engineering priority is identifying which landmark/confidence component causes interruptions before selecting a change in evidence handling. The current aggregate score cannot establish that cause. Preserve this run as the fixed-settings evaluation; use separate development runs for any subsequent tuning.

Recorder follow-up: the right shoulder left the frame at the top position in pilot2. This supplies a plausible acquisition-related explanation for evidence failures; the saved aggregate confidence does not independently identify the failing landmark. Preserve these results as a framing failure case. Pilot3 contains replacement recordings reported to keep the entire body visible; evaluate those separately with the same configuration.
