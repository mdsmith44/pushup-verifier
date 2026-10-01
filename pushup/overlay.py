"""Diagnostic drawing for observed landmarks, not a form verdict."""


def annotate(frame, points, elbow, body, confidence, timestamp, side, config):
    import cv2

    # Resize the display only; inference and angle calculations use the original.
    height, width = frame.shape[:2]
    scale = min(1.0, 1280 / width, 960 / height)
    width, height = max(2, int(width * scale) // 2 * 2), max(2, int(height * scale) // 2 * 2)
    canvas = cv2.resize(frame, (width, height))
    sx, sy = width / frame.shape[1], height / frame.shape[0]
    if points:
        coords = [(round(x * sx), round(y * sy)) for x, y in points]
        reliable = confidence >= config.min_confidence
        color = (60, 220, 60) if reliable else (0, 165, 255)
        for a, b in [(0, 1), (1, 2), (0, 3), (3, 4)]:
            cv2.line(canvas, coords[a], coords[b], color, 3, cv2.LINE_AA)
        for point, label in zip(coords, ["S", "E", "W", "H", "A"]):
            cv2.circle(canvas, point, 6, color, -1, cv2.LINE_AA)
            cv2.putText(canvas, label, (point[0] + 8, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
    # A separate header prevents the diagnostic text from hiding joints.
    canvas = cv2.copyMakeBorder(canvas, 138, 0, 0, 0, cv2.BORDER_CONSTANT, value=(20, 20, 20))
    elbow_text = f"{elbow:.1f} deg" if elbow != "" else "unknown"
    body_text = f"{body:.1f} deg" if body != "" else "unknown"
    lines = [
        f"t={timestamp:.3f}s | anatomical {side} side | raw measurements",
        f"Elbow: {elbow_text} | depth <= {config.bottom_angle:g} | top >= {config.top_angle:g}",
        f"Body: {body_text} | confidence: {confidence:.3f} (minimum {config.min_confidence:g})",
        "S shoulder / E elbow / W wrist / H hip / A ankle | not a rep verdict",
    ]
    font_scale = min(0.58, width / 1500)
    for index, line in enumerate(lines):
        cv2.putText(canvas, line, (12, 27 + index * 30), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (245, 245, 245), 1, cv2.LINE_AA)
    return canvas
