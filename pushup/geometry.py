"""Image-plane geometry; pass pixel coordinates, not unscaled normalized XY."""

import math


def angle(a, b, c):
    """Return angle ABC in degrees; reject missing or degenerate geometry."""
    if not all(math.isfinite(v) for point in (a, b, c) for v in point):
        raise ValueError("Coordinates must be finite")
    u = (a[0] - b[0], a[1] - b[1])
    v = (c[0] - b[0], c[1] - b[1])
    scale = math.hypot(*u) * math.hypot(*v)
    if scale < 1e-12:
        raise ValueError("Coincident landmarks")
    cosine = max(-1.0, min(1.0, (u[0]*v[0] + u[1]*v[1]) / scale))
    return math.degrees(math.acos(cosine))
