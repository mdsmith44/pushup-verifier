# Evaluation plan

Freeze configuration before evaluating held-out sessions. Save both methods' reports from the same pose CSVs. Record camera setup, model source/hash, software versions, and hardware.

1. Count error: absolute difference between manually labeled completed repetitions and algorithmically completed attempts (accepted + rejected). Also report accepted-rep count error separately.
2. Detection/segmentation: match predicted and manual attempt intervals one-to-one by greatest temporal overlap, with a predeclared overlap requirement (initial proposal: intersection-over-union ≥0.5). Report unmatched manual attempts and unmatched predictions. Do not evaluate form only on the easy matched cases without reporting misses.
3. Form: among matched, assessable attempts, report rejection precision and recall and confusion counts. Preserve human-uncertain labels separately.
4. Coverage: report the fraction of labeled attempts receiving an assessable decision and the duration of uncertainty intervals. An interrupted attempt is not proof of exactly one hidden rep.
5. Delay: compare decision timestamps with manually marked return-to-top times for matched attempts. Report median and range. Measure wall-clock throughput independently; video-time delay is not compute latency.
6. Robustness: break down clear side-view and stress-test clips. Include failures and paired baseline/temporal differences. Small-sample results are exploratory.

Planned final artifacts: per-clip metrics CSV, confusion tables, elbow-angle traces with phase transitions, an annotated video, and a short report. None are research results until real recordings have been evaluated.
