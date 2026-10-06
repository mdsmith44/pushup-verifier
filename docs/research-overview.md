# Research findings and reproducible experiments

This document preserves the pilot findings and detailed command-line experiments behind the deployed app. The standard decision-engine defaults and the frozen configuration used by the app are distinct; the app uses the 140-degree candidate with separate alignment and partial-start reporting.

## Research question

**Does smoothing and persistent threshold evidence reduce false decisions without suppressing real movement transitions?**

Immediate mode uses raw measurements. Temporal mode applies an elapsed-time exponential moving average and requires threshold conditions to persist for 0.1 seconds. Both use the same confidence checks and movement sequence.

## Initial pilot findings

| Development clip | Manual observation | Immediate mode | Temporal mode |
|---|---|---|---|
| Full repetitions | 5 completed repetitions | 5 accepted | 2 accepted; 1 unfinished tracked attempt |
| Shallow repetitions | 3 attempts, all insufficient depth | 3 rejected for depth | 1 rejected for depth; 1 unfinished tracked attempt |
| Visibility challenge | 4 valid attempts reported by the recorder; attempts 2 and 4 obscured | 2 interrupted tracked attempts; none accepted/rejected | No attempts established; evidence gaps recorded |

**These are exploratory development results, not accuracy claims.** The top threshold was tuned using the full-repetition clip. The first batch has 12 approximate recorder-supplied attempt intervals; later batches have recorder-supplied counts and sequences. Independent adjudication and timestamped matching for the later batches remain pending. An unfinished or interrupted tracked attempt can span or omit multiple actual movements.

The immediate method agrees with the manual counts on the first two clips. The temporal method suppresses later peaks near the top threshold and can merge several movements into one unfinished attempt. On the visibility clip, neither method produced an assessable decision for the clear attempts. A single low-confidence frame currently interrupts an active attempt.

These failures are part of the research: they expose tradeoffs between noise suppression, decision coverage, and faithful segmentation. See [pilot findings and limitations](pilot-results.md) and the [evaluation plan](evaluation.md).

## Follow-up findings and current experiments

A 140° top threshold improved temporal-mode counts on the original full and shallow clips. We froze that configuration before processing two new batches. Pilot2 exposed a recording problem: the shoulder left the frame. Pilot3 improved framing, but per-landmark diagnostics showed that ankle visibility still caused most interruptions. Even with reliable arm evidence, the original all-joint confidence gate reset the whole attempt.

Two opt-in changes address different failures:

- **Separate alignment:** use shoulder–elbow–wrist confidence to track movement, and shoulder–hip–ankle confidence to assess alignment. Missing alignment evidence makes form unassessable without discarding an otherwise observable movement.
- **Partial start:** report an initial descent and return when the starting top was not verified. These returns remain unassessable and are counted separately from complete top-anchored movements. The policy requires a 10° measured descent and cannot restart after a tracking interruption.

| Pilot3 clip | Recorder's attempts | Frozen baseline completed decisions | Experimental top-anchored completions | Partial-start returns | Interrupted |
|---|---:|---:|---:|---:|---:|
| Full | 5 | 3 | 5 | 0 | 0 |
| Shallow | 3 | 2 | 2 | 1 | 0 |
| Mixed | 5 | 1 | 3 | 1 | 1 |

**Completion does not mean valid form.** Of the five full-clip completions, three were accepted and two had insufficient alignment evidence. The shallow clip had two rejected completions and one unassessable partial start. The mixed clip had one rejected completion, two completed-but-unassessable movements, one unassessable partial-start return, and one interrupted attempt. Its completed-unassessable movements also lacked the required depth evidence. Exact correspondence to manual attempts still requires timestamped matching.

These changes improve visibility into what the system observed; they do not establish accuracy or generalization. The original frozen evaluations are preserved. Single-frame dropout tolerance and an ankle-jump guard were also explored: neither is enabled in the normal pipeline, and the jump guard reduced tracking coverage. Landmark sensitivity remains a documented limitation rather than a solved problem.

See the [pilot2 evaluation](pilot2-evaluation.md), [pilot3 evaluation](pilot3-evaluation.md), [confidence diagnosis](pilot3-diagnosis.md), [separate-alignment experiment](separate-alignment.md), and [partial-start experiment](partial-start.md).

## Fresh-video validation milestone

After the experimental policies were implemented, a new recording (`pilot3B_mixed`) was evaluated using the fixed 140° temporal configuration with separate alignment and partial-start reporting enabled. Its expected sequence was supplied before processing. All five movements were completed, with decisions **accepted → rejected for depth → accepted → rejected for depth → accepted**. There were no evidence gaps, unassessable decisions, or partial starts.

This is count-and-order agreement on one new clip from the same participant, not a general accuracy estimate. Predicted intervals have not yet been independently matched to manual timestamps. The baseline temporal policy at the same thresholds also succeeds on this clip, so it does not demonstrate the benefit of the experimental uncertainty policies. See the [validation report and saved results](pilot3B-validation.md).

## Observable rules

| Parameter | Default setting |
|---|---:|
| Top elbow angle | ≥145° |
| Departure from top | ≤130° |
| Bottom elbow angle | ≤90° |
| Body alignment angle | ≥160° |
| Minimum landmark confidence | 0.6 |
| Maximum observation gap | 0.25 seconds |
| Temporal persistence | 0.10 seconds |
| Smoothing time constant | 0.08 seconds |

The 145° top setting is a relaxed development criterion for the existing recordings, not proof of full elbow extension. A projected 90° elbow angle is also not geometrically equivalent to the upper arm being parallel to the floor. Camera perspective, landmark placement, and occlusion affect these measurements.

The default confidence gate uses the minimum visibility/presence score across the selected shoulder, elbow, wrist, hip, and ankle. The opt-in separate-alignment policy uses distinct arm and alignment gates as described above. It is not a calibrated probability that an angle or decision is correct. See the complete [rubric](rubric.md).

## Run on your own video

The video workflow was exercised with Python 3.12 in a Conda environment on Linux/WSL. Use one environment for the whole project:

```bash
conda create -n pushup-verifier python=3.12 pip
conda activate pushup-verifier
python -m pip install -r requirements/video.txt
```

On Ubuntu/WSL, if MediaPipe reports a missing `libGLESv2.so.2`:

```bash
sudo apt update
sudo apt install libgles2
```

Download the **Full Pose Landmarker** `.task` bundle from the [official MediaPipe model page](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker#models), and place it at `models/pose_landmarker_full.task`. Place your own video in `data/raw/`. Videos and model weights are excluded from the repository.

```bash
python -m pushup.extract \
  data/raw/your_video.MOV \
  --model models/pose_landmarker_full.task \
  --side right \
  --output data/observations/your_video.csv \
  --annotated-video results/your_video_overlay.mp4 \
  --review-frame results/your_video_max_angle.png

python -m pushup.replay \
  data/observations/your_video.csv \
  --mode immediate \
  --output results/your_video_immediate.json

python -m pushup.replay \
  data/observations/your_video.csv \
  --mode temporal \
  --output results/your_video_temporal.json
```

Select the anatomical side facing the camera. Extraction requires new output filenames and will not intentionally overwrite existing files. Replay applies the settings in `config/default.json` and records them in each report. Existing overlays retain the thresholds shown when they were generated.

The annotated preview uses nominal FPS without audio; its displayed timestamps come from the source video. The review PNG selects the greatest reliable raw elbow angle, not a guaranteed fully extended pose. `.MOV` decoding depends on the installed codecs, and the extractor requires increasing source timestamps.

## Run the experimental policies

The defaults above remain unchanged. For the 140° temporal candidate with both experimental policies, extract a new diagnostic CSV with per-joint confidence, then replay it:

```bash
python -m pushup.extract \
  data/raw/your_video.MOV \
  --model models/pose_landmarker_full.task \
  --side right \
  --config config/pilot2_frozen.json \
  --include-confidence --include-landmarks \
  --output data/observations/your_video_diagnostic.csv

python -m pushup.replay \
  data/observations/your_video_diagnostic.csv \
  --mode temporal --config config/pilot2_frozen.json \
  --separate-alignment --partial-start \
  --output results/your_video_experimental.json
```

`completed_movements` counts top-anchored completions, including rejected or unassessable form. `partial_start_returns` is separate. An attempt's `completed` field records whether a return to top was observed; `start_observed` distinguishes a verified starting top from a partial start. `counts.accepted` remains the valid-form decision count. Alignment-uncertain timestamps are reported separately from movement evidence-gap intervals. An empty gap list alone does not mean form was assessable.

## Next research steps

- Complete timestamped matching for the follow-up recordings and report missed movements alongside form decisions.
- Review remaining depth disagreements and whole-pose loss in the mixed clip.
- Extend the fresh-clip validation with independent timing labels and recordings that exercise uncertainty policies.
- Expand beyond one participant and camera setup before making generalization claims.
MediaPipe performs the pretrained perception step. The project work focuses on geometry, stateful procedure verification, diagnostics, and transparent evaluation. See [MediaPipe documentation](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) for model details.
