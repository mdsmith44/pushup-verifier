"""Optional MediaPipe video adapter. Validate on pilot footage before use."""

import argparse
import csv
import math
import json
from pathlib import Path
from .geometry import angle
from .engine import Config
from .overlay import annotate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--side", choices=["left", "right"], required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--annotated-video", type=Path, help="Optional MP4 diagnostic video (no audio)")
    parser.add_argument("--review-frame", type=Path, help="Optional PNG at the greatest reliable raw elbow angle")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "config/default.json")
    args = parser.parse_args()
    if not args.video.is_file() or not args.model.is_file():
        parser.error("Video and local .task model must exist")
    outputs = [p for p in (args.output, args.annotated_video, args.review_frame) if p is not None]
    protected = {args.video.resolve(), args.model.resolve(), args.config.resolve()}
    if any(p.exists() or p.resolve() in protected for p in outputs) or len({p.resolve() for p in outputs}) != len(outputs):
        parser.error("Choose new, distinct output files that do not replace inputs")
    if args.annotated_video and args.annotated_video.suffix.lower() != ".mp4":
        parser.error("Annotated video must use .mp4")
    if args.review_frame and args.review_frame.suffix.lower() != ".png":
        parser.error("Review frame must use .png")
    config = Config(**json.loads(args.config.read_text(encoding="utf-8")))
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        parser.error("Install requirements-video.txt in a dedicated environment first")
    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_poses=2)
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        cap.release()
        parser.error("Cannot open video")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    indices = (11, 13, 15, 23, 27) if args.side == "left" else (12, 14, 16, 24, 28)
    previous_ms = -1
    count = 0
    video_writer = None
    best_frame, best_angle, best_time = None, -1, None
    fps = cap.get(cv2.CAP_PROP_FPS)
    if args.annotated_video and (not math.isfinite(fps) or fps <= 0):
        cap.release()
        parser.error("Video has no usable frame rate for MP4 preview")
    try:
        with mp.tasks.vision.PoseLandmarker.create_from_options(options) as model, args.output.open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["timestamp", "elbow_angle", "body_angle", "confidence"])
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
                if not math.isfinite(timestamp) or round(timestamp) <= previous_ms:
                    raise ValueError("Video timestamps are invalid/non-increasing; output is incomplete")
                previous_ms = round(timestamp)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                result = model.detect_for_video(image, previous_ms)
                elbow, body, confidence = "", "", 0
                draw_points = None
                if len(result.pose_landmarks) == 1:
                    landmarks = [result.pose_landmarks[0][i] for i in indices]
                    h, w = frame.shape[:2]
                    points = [(p.x*w, p.y*h) for p in landmarks]
                    scores = [min(p.visibility or 0, p.presence or 0) for p in landmarks]
                    if all(0 <= p.x <= 1 and 0 <= p.y <= 1 for p in landmarks) and all(math.isfinite(s) for s in scores):
                        try:
                            elbow = angle(*points[:3])
                            body = angle(points[0], points[3], points[4])
                            confidence = min(scores)
                            draw_points = points
                        except ValueError:
                            elbow, body, confidence = "", "", 0
                writer.writerow([previous_ms / 1000, elbow, body, confidence])
                if args.annotated_video or args.review_frame:
                    display = annotate(frame, draw_points, elbow, body, confidence, previous_ms / 1000, args.side, config)
                    if args.annotated_video:
                        if video_writer is None:
                            args.annotated_video.parent.mkdir(parents=True, exist_ok=True)
                            video_writer = cv2.VideoWriter(str(args.annotated_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (display.shape[1], display.shape[0]))
                            if not video_writer.isOpened():
                                raise RuntimeError("Could not initialize MP4 writer; outputs may be incomplete")
                        video_writer.write(display)
                    if args.review_frame and elbow != "" and confidence >= config.min_confidence and elbow > best_angle:
                        best_frame, best_angle, best_time = display.copy(), elbow, previous_ms / 1000
                count += 1
    finally:
        cap.release()
        if video_writer is not None:
            video_writer.release()
    if count == 0:
        raise ValueError("Video contained no decoded frames")
    print(f"Saved {count} observations to {args.output}. Review against video before interpreting decisions.")
    if args.annotated_video:
        print(f"Saved annotated preview to {args.annotated_video}. Playback uses nominal FPS; displayed times are source timestamps. No audio.")
    if args.review_frame:
        if best_frame is None:
            print("No reliable elbow observation; no review frame saved.")
        else:
            args.review_frame.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(args.review_frame), best_frame):
                raise RuntimeError("Could not save review frame")
            print(f"Saved maximum-angle review frame to {args.review_frame}: {best_angle:.2f} degrees at {best_time:.3f}s. This is not a verified top position.")


if __name__ == "__main__":
    main()
