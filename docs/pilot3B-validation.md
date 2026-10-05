# Fresh-video validation: pilot3B mixed

October 4, 2026. Code revision: `5f47a4c50206cd9e01ae55354543b2dfba4164cc`.

The recorder supplied a new clip with a longer pause before the first pushup and the expected sequence full–shallow–full–shallow–full before processing. Anatomical right side was assumed consistent with previous recordings. Used MediaPipe Full, `config/pilot2_frozen.json`, temporal mode, `--separate-alignment`, and `--partial-start`. No settings were changed after seeing this video. Extracted 541 observations. The saved [report](validation-reports/pilot3B_mixed.json) contains all configuration values.

| Predicted attempt | Start–end (seconds) | Expected sequence position | Decision |
|---|---|---|---|
| 1 | 2.123–3.758 | Full | Accepted |
| 2 | 5.392–7.058 | Shallow | Rejected: depth evidence absent |
| 3 | 8.460–10.393 | Full | Accepted |
| 4 | 11.995–13.728 | Shallow | Rejected: depth evidence absent |
| 5 | 15.162–16.997 | Full | Accepted |

Five top-anchored completions, three accepted, two rejected, zero unassessable decisions, zero partial-start returns, and no movement or alignment evidence gaps. Count and decision order agree with the recorder's stated sequence. The intervals above are predictions, not manual ground truth; timestamped manual matching remains pending.

The baseline temporal policy at the same 140-degree configuration also yields three accepted and two rejected. This clip does not exercise the missing-alignment or partial-start branches, so it cannot establish their effectiveness. The result supports feasibility under these recording conditions; one new clip from the same participant is not a general accuracy estimate. Preserve earlier failures alongside this result. No extra threshold tuning was performed.
