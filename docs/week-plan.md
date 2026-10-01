# One-week plan

Budget: about 20–30 focused hours. The pose model is pretrained; your learning focus is geometry, temporal reasoning, evaluation, and a reproducible video pipeline.

Active scope: conventional top → bottom → top pushups with a 90° elbow-depth criterion. Hand-release/T-position work is deferred. The demo should show the elbow angle and a 90° reference, and the analysis should plot raw and smoothed angles over time.

| Day | Focus | Deliverable |
|---|---|---|
| 1 | Understand the rubric, record three pilots, check pose landmarks | Reliable camera view and anatomical side selection |
| 2 | Examine angle/visibility traces; collect and label sessions | Manifest, labels, and development/test split |
| 3 | Inspect the reference state machine; compare its decisions with video | First manually verified replay |
| 4 | Tune development thresholds; compare immediate and temporal methods | Frozen configuration and documented hypotheses |
| 5 | Evaluate held-out sessions | Count errors, rep decisions, coverage, and latency |
| 6 | Add video overlays showing skeleton, phase, and reasons | Understandable local demo |
| 7 | Write results, failure cases, and reproduction steps | Portfolio-ready repository and short demo recording |

Questions to investigate: Why do image aspect ratio and camera angle matter? Can smoothing erase brief valid bottom positions? Can an unknown interval hide several reps? Are gains due to fewer decisions? Does the method generalize to another session or person?

Keep neural-network training, official military test rules, cloud deployment, and multi-person tracking out of week one. A learned sequence classifier or separate smoothing/persistence ablations can follow once the baseline is measured.
