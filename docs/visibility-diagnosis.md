# Visibility pilot diagnosis

## Follow-up: manual review and coordinate experiment

The recorder observed an elbow landmark shift near 3.8–4.1 s and an ankle tracking error as an obstruction moved across the image after attempt 3. These observations support investigating tracking quality, but do not establish exact joint angles.

Correction to the initial conversational interpretation: original measurements already contain body angles below 160 degrees at 7.937 s (159.12), 7.970 s (156.49), and 8.872 s (158.90), with confidence above 0.6. These precede the reported obstruction and explain the immediate-mode alignment rejection. They require frame-specific review; they do not by themselves prove actual poor form. The obstruction produces another below-threshold angle at 9.438 s, when confidence is already below the gate. It therefore cannot explain the immediate-mode rejection finalized at 9.338 s in the 140-degree experiment.

Added optional `--include-landmarks` extraction (pixel coordinates) and `python examples/ankle_guard.py` for offline diagnosis. The coordinate extraction reproduced all 416 original timestamps, angles, and confidence values exactly. The candidate guard measures ankle motion relative to the hip and projected hip-to-ankle length changes, normalized by previous length and elapsed time. A fixed exploratory threshold of 3 leg-lengths/second flagged 72 frames, including several before obstruction. It flags the transition at 9.405 s before confidence fails, but reduces tracking coverage (140-degree immediate: 0 accepted / 0 rejected / 2 unable; temporal: no tracked attempts). This is not evidence of improvement and the guard is not enabled in the normal pipeline. Sustained wrong coordinates and slow drift can evade it, while projection changes and hip errors can trigger it. Defaults remain unchanged. Review the earlier three frames before tuning the guard or alignment threshold.

Run `python examples/inspect_visibility.py` with matplotlib installed and the private observations available. It writes a three-panel plot and per-frame state trace under `results/`. It replays the actual engine; both output counts match the saved reports. No thresholds or engine behavior were changed.

## Clear attempt 1: 3.00–4.75 seconds

Immediate mode starts an attempt at 3.335 s. Confidence falls to 0.498 at 3.502 s, below the 0.6 gate, then recovers at 3.535 s. This single-frame failure aborts the attempt. Of 53 observations inside the manual interval, 52 pass the evidence gate. Temporal mode first gets a filtered departure angle below 130 at 3.435 s; the confidence failure arrives before the required 0.1 seconds elapse, resetting it before an attempt starts. The maximum reliable raw elbow angle from 4.4 to 5.0 s is only 144.622 degrees, so the return cannot establish a new top at the configured 145-degree threshold.

## Clear attempt 3: 7.50–9.25 seconds

All 53 observations inside the manual interval pass the evidence gate. A raw top crossing at 7.170 s (145.375 degrees) arms immediate mode; the filtered angle is only 144.128 degrees at that moment. Temporal mode never establishes a top before this attempt. Immediate mode starts tracking at 7.670 s, but does not see a qualifying return. Between 8.9 and 9.438 s, the maximum reliable elbow angle is 141.332 degrees. It remains active past the manually labeled end and is interrupted by confidence 0.527 at 9.438 s.

## Interpretation

Two independent problems are visible: abrupt reset after one low-confidence frame, and measured top angles that do not consistently reach the configured threshold. The third attempt's eventual interruption occurs after its manual end; its primary completion failure is the missing top crossing. High confidence does not prove that the elbow angle is accurate. The aggregate confidence CSV cannot identify which landmark caused a failure. Review the corresponding video frames before choosing between pose/camera improvements and threshold calibration. A future brief-gap policy must still distinguish missing evidence from observed valid technique and be tested against the longer occlusions. These are development findings from one recording, not generalization results.
