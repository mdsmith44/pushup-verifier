# Recording guide

## First three pilot clips

Use a stable phone or webcam approximately perpendicular to your side, with shoulders, elbows, wrists, hips, and ankles visible throughout. Leave margin around your body and use clear lighting. Prefer a consistent frame rate such as 30 fps. Keep other people out of frame.

1. A short set of 3–5 ordinary full repetitions.
2. A short set containing intentionally shallow repetitions.
3. A clip with a visibility problem, such as partial cropping, to exercise abstention.

These are conventional pushups; no T-position or hand release is required. Keep the camera-facing shoulder, elbow, and wrist unobstructed. Include some near-threshold attempts later to investigate 90° measurement sensitivity, without relying on the performer to reproduce an exact angle.

Start and end in a visible top position for about one second. Use short, comfortable sets; data quality matters more than repetition volume. Save originals under `data/raw/`. The pilot goal is to confirm pose quality and side selection, not claim accuracy.

## Full study

Aim for 24 short clips over four recording sessions, roughly six clips per session. Use the first two sessions for development and the last two for testing. Include ordinary reps, shallow reps, mixed sets, pauses, incomplete endings, and difficult visibility. Vary lighting and modest camera placement changes. Keep a clear side view for the primary test; label oblique views as a separate stress test.

If other volunteers participate, reserve at least one person for testing when feasible. A study with only your own videos is a single-person feasibility study. Keep all versions and frames of a recording in the same split.

## Manual labels

Fill `data/manifest.csv`, then annotate each actual attempted repetition in `data/labels.csv` with start/end times, depth and alignment assessments, and assessability. Use slow-motion video review independent of model output. Do not generate ground truth by applying the same landmark thresholds being evaluated.

Mark uncertain human judgments as `uncertain`, rather than forcing a binary label. Note whether the video was truncated or the movement actually failed to return to top. Establish labels before inspecting test predictions. Publish video only where you have permission; raw video is excluded from Git by default.

Times are seconds from the start of the source video. For conventional pushups, label the start of descent through the return to the top; adjacent attempts may share a boundary. Record approximate boundaries as such in `notes` and refine them during frame-by-frame review. `completed` describes completion of the movement, not a valid-form decision. Keep a recorder's overall validity judgment in `notes` when depth and alignment have not been separately reviewed; use `uncertain` for those pending component labels. `assessability` describes human video review (`assessable` or `uncertain`), not the model's confidence score. An obscured attempt does not establish the exact interval of occlusion.
