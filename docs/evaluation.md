# Evaluation plan

Freeze configuration before evaluating held-out sessions. Save both methods' reports from the same pose CSVs. Record camera setup, model source/hash, software versions, and hardware.

1. Count error: compare manually labeled completed movements with `completed_movements` for experimental reports, which includes completed-but-unassessable form. Legacy reports lack that field; accepted + rejected is their completed-decision count. Report partial-start returns separately rather than silently adding them to verified top-anchored completions. Also report accepted-rep count error separately.
2. Detection/segmentation: match predicted and manual attempt intervals one-to-one by greatest temporal overlap, with a predeclared overlap requirement (initial proposal: intersection-over-union ≥0.5). Report unmatched manual attempts and unmatched predictions. Do not evaluate form only on the easy matched cases without reporting misses.
3. Form: among matched, assessable attempts, report rejection precision and recall and confusion counts. Preserve human-uncertain labels separately.
4. Coverage: report the fraction of labeled attempts receiving an assessable decision and the duration of uncertainty intervals. An interrupted attempt is not proof of exactly one hidden rep.
5. Delay: compare decision timestamps with manually marked return-to-top times for matched attempts. Report median and range. Measure wall-clock throughput independently; video-time delay is not compute latency.
6. Robustness: break down clear side-view and stress-test clips. Include failures and paired baseline/temporal differences. Small-sample results are exploratory.

Available artifacts include pilot interval comparisons, angle/state traces, frozen evaluation reports, and the annotated pilot3B validation demo. General form accuracy and cross-person performance remain unestablished. The bounded [next validation plan](next-validation.md) describes the next extension.
