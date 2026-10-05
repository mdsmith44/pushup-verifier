# Third pilot: replacement recordings with full-body framing

The recorder reported that the right shoulder left the frame at the top in pilot2 and supplied pilot3 replacements with the entire body visible. Same expected outcomes confirmed: five full repetitions; three shallow attempts; five mixed attempts in full–shallow–full–shallow–full order. Anatomical right side was used as in previous batches. Per-attempt manual timestamps are pending.

Used the unchanged `config/pilot2_frozen.json` with temporal mode and MediaPipe Full. No dropout tolerance or ankle guard. Reports are in `pilot3-reports/`; private coordinates and observations remain excluded from Git. Pilot2 remains documented as a framing failure case rather than being replaced silently.

| Clip | Expected accepted/rejected | Actual accepted/rejected/unable | Unreliable observations |
|---|---|---|---|
| Full | 5 / 0 | 3 / 0 / 1 | 8 / 392 (2.0%) |
| Shallow | 0 / 3 | 0 / 2 / 0 | 0 / 291 (0%) |
| Mixed | 3 / 2 | 0 / 1 / 3 | 23 / 502 (4.6%) |

Unreliable means missing angles or confidence below 0.6. For comparison, pilot2 had 24/377 (6.4%), 48/326 (14.7%), and 29/510 (5.7%) unreliable observations, respectively. These are new performances, so the improvement cannot be causally attributed to framing alone.

The shallow clip has no evidence gaps but only establishes the initial top at 2.053 s, then starts its first tracked attempt at 3.388 s (confirmed at 3.488 s). This suggests the initial movement was missed because a top had not been established. The mixed clip first establishes a top at 3.770 s; three later attempts are interrupted by missing evidence. Full clip tracking is interrupted at 6.683 s and additional confidence failures occur later. Attempt segments are not guaranteed to match actual repetitions one-to-one. All three rejected segments across shallow/mixed clips cite missing bottom-angle evidence; all four interrupted segments across full/mixed clips cite missing pose evidence. Matching sequence and exact missed-attempt identity requires manual timestamps.

Next: examine start-of-video top recognition and remaining confidence failures using these existing clips. Keep this evaluation frozen; do not present later tuning on these recordings as independent validation. No further recordings are needed for the next diagnostic step.
