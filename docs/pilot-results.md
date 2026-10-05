# Pilot findings — October 1, 2026

Three single-person development recordings were processed with MediaPipe Full and anatomical right-side landmarks. These recordings were used for debugging and threshold selection, not held-out testing. Raw videos, extracted landmark/angle data, and identifiable frames are not published.

| Clip | Recorder's manual observation | Immediate A/R/U | Temporal A/R/U |
|---|---|---|---|
| Full reps | 5 completed repetitions | 5 / 0 / 0 | 2 / 0 / 1 |
| Shallow reps | 3 attempts, all shallow | 0 / 3 / 0 | 0 / 1 / 1 |
| Visibility | 4 valid attempts reported; 2 and 4 obscured | 0 / 0 / 2 | 0 / 0 / 0 |

A = accepted, R = rejected, U = an established tracked attempt that became unassessable. These are algorithmic segments, not guaranteed one-to-one matches with actual repetitions. Zero U does not imply full assessability: temporal mode failed to establish any attempt in the visibility clip. Both methods recorded the same ten evidence-gap intervals there.

## What was learned

1. Selecting the camera-facing anatomical side matters. Left-side extraction on the first clip remained uncertain; right-side extraction passed the confidence gate throughout.
2. No raw elbow measurement in that clip reached the original 160° top threshold. The pilot top threshold was relaxed to 145°, with departure at 130° and depth at 90°. This adjustment prevents treating the same recording as independent test evidence.
3. At the five returns to top, maximum raw/smoothed angles were approximately 148.8/147.3°, 146.2/145.4°, 146.0/143.6°, 146.1/144.9°, and 146.0/144.7°. Smoothing suppressed the final three qualifying raw peaks. Their raw crossings also failed the 0.1-second persistence condition when tested without smoothing.
4. Immediate mode identified five full attempts and three shallow attempts, rejecting all shallow attempts for depth. Agreement is based on recorder review and requires timestamped confirmation.
5. In the visibility clip, immediate mode interrupted its first tracked attempt after a roughly one-frame evidence failure. Neither method produced an assessable decision for the manually reported clear attempts. Abstention alone is not successful performance.

## Evidence and limits

Selected replay reports are stored in `pilot-reports/`; each includes the configuration used. These reports can be inspected without private footage, but independent reproduction of the pilot predictions requires that footage and its derived observations. Synthetic examples remain freely runnable. Approximate recorder-supplied timestamps for all 12 attempts across the three clips are now in `../data/labels.csv`. Updated visibility intervals are 3.00–4.75, 5.00–7.00, 7.50–9.25, and 10.25–12.00 seconds, replacing the earlier shared-boundary estimates. All four visibility attempts were reported valid; attempts 2 and 4 were obscured. All three shallow attempts are labeled insufficient depth. Separate component review where marked uncertain and precise boundary confirmation remain pending. These are development annotations collected after viewing predictions; interval matching has not yet been evaluated. Inter-rater agreement has not yet been collected. No accuracy, clinical, military-scoring, or cross-person generalization claim is made.

Next: align manual attempt intervals with predictions, measure coverage as well as errors, evaluate temporal components separately, and test frozen settings on new sessions.
