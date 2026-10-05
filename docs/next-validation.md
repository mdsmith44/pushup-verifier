# Next milestone: small robustness evaluation

The initial portfolio milestone is complete. This optional extension tests transfer beyond the development recordings; it is not a requirement for showcasing the existing project.

## Freeze before recording

Use temporal mode, `config/pilot2_frozen.json`, `--separate-alignment`, and `--partial-start`. Record the current Git commit and camera-facing anatomical side. Do not adjust thresholds after viewing these predictions. Keep later fixes separate as development experiments.

## Collect only three short clips

Prefer a second consenting participant in the same camera setup. If unavailable, use the original participant with a different camera distance or lighting condition, changing one factor at a time. That alternative evaluates setup robustness, not cross-person generalization.

1. Five ordinary full repetitions.
2. Three intentionally shallow attempts.
3. Five mixed attempts: full, shallow, full, shallow, full.

Keep the whole body in frame with margin, use a stable side view, and pause at the top for about one second before starting. Use comfortable sets. Keep raw footage private unless separately chosen for publication. No additional occlusion clip is needed for this initial extension.

## Label before running predictions

Record what actually happened, even if it differs from the intended sequence. Add rows to `data/manifest.csv` with a distinct person/session identifier and evaluation split. Add manual start/end times to `data/labels.csv`, plus completion, depth, alignment, assessability, and uncertainty notes. Start is visible descent; end is return to top. Do not copy predicted timestamps into manual labels.

## Report success and failure separately

- Match manual and predicted intervals one-to-one using the existing IoU >=0.5 rule. List missed manual movements and unmatched predictions.
- Report top-anchored completions, partial-start returns, and interrupted attempts separately.
- Compare accepted/rejected form only when manual evidence supports a form judgment; report unassessable coverage alongside those comparisons.
- A successful clip requires count and sequence agreement without extra or missed matched attempts. Matching aggregate counts alone is insufficient. Publish failures alongside successes and avoid a general accuracy claim from this small sample.

Stop after these three clips and write a short result table. Decide on another engineering change only if a specific recurring failure justifies it; avoid tuning indefinitely on the evaluation set.
