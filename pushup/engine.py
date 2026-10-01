"""Reference rep segmentation with explicit evidence gaps and end truncation."""

from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class Config:
    top_angle: float = 145
    departure_angle: float = 130
    bottom_angle: float = 90
    alignment_angle: float = 160
    min_confidence: float = 0.6
    max_gap: float = 0.25
    persistence: float = 0.1
    smoothing_tau: float = 0.08

    def __post_init__(self):
        if not all(math.isfinite(v) for v in asdict(self).values()):
            raise ValueError("Configuration values must be finite")
        if not 0 < self.bottom_angle < self.departure_angle < self.top_angle <= 180:
            raise ValueError("Require 0 < bottom < departure < top <= 180")
        if not 0 <= self.alignment_angle <= 180 or not 0 <= self.min_confidence <= 1:
            raise ValueError("Invalid alignment/confidence threshold")
        if self.max_gap <= 0 or self.persistence < 0 or self.smoothing_tau < 0:
            raise ValueError("Invalid timing configuration")


class Verifier:
    def __init__(self, config=None, mode="temporal"):
        if mode not in {"immediate", "temporal"}:
            raise ValueError("Unknown mode")
        self.config = config or Config()
        self.mode = mode
        self.phase = "await_top"
        self.previous = None
        self.filtered = None
        self.holds = {}
        self.active = None
        self.attempts = []
        self.uncertainty = []
        self.open_gap = None
        self.closed = False

    def held(self, key, condition, time):
        if not condition:
            self.holds.pop(key, None)
            return False
        since = self.holds.setdefault(key, time)
        duration = self.config.persistence if self.mode == "temporal" else 0
        return time - since + 1e-9 >= duration

    def complete(self, time, status, reasons):
        self.attempts.append({"start_s": self.active["start_s"], "end_s": time,
                              "status": status, "reasons": reasons})
        self.active = None

    def interrupt(self, time, start):
        if self.active is not None:
            self.complete(time, "unable_to_assess", ["Required pose evidence missing."])
        if self.open_gap is None:
            self.open_gap = start
        self.phase, self.filtered = "await_top", None
        self.holds.clear()

    def update(self, time, elbow, body, confidence):
        if self.closed:
            raise ValueError("Cannot update a finalized verifier")
        if not math.isfinite(time) or time < 0 or (self.previous is not None and time <= self.previous):
            raise ValueError("Timestamps must be finite, nonnegative, and strictly increasing")
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Confidence must be finite and between zero and one")
        for value in (elbow, body):
            if value is not None and (not math.isfinite(value) or not 0 <= value <= 180):
                raise ValueError("Angles must be blank or finite values in [0, 180]")
        previous = self.previous
        delta = 0 if previous is None else time - previous
        self.previous = time
        if previous is not None and delta > self.config.max_gap + 1e-9:
            self.interrupt(time, previous)
        if elbow is None or body is None or confidence < self.config.min_confidence:
            self.interrupt(time, time)
            return
        if self.open_gap is not None:
            self.uncertainty.append({"start_s": self.open_gap, "end_s": time})
            self.open_gap = None
        tau = self.config.smoothing_tau if self.mode == "temporal" else 0
        if self.filtered is None or tau == 0:
            self.filtered = (elbow, body)
        else:
            alpha = 1 - math.exp(-delta / tau)
            self.filtered = tuple(old + alpha * (new - old) for old, new in zip(self.filtered, (elbow, body)))
        elbow, body = self.filtered
        top = self.held("top", elbow >= self.config.top_angle, time)
        departure = self.held("departure", elbow <= self.config.departure_angle, time)

        if self.phase == "await_top":
            if top:
                self.phase = "top"
            return
        if self.phase == "top" and departure:
            self.active = {"start_s": self.holds["departure"], "bottom": False, "bad_alignment": False}
            self.phase = "attempt"
        if self.phase == "attempt":
            if self.held("bottom", elbow <= self.config.bottom_angle, time):
                self.active["bottom"] = True
            if self.held("alignment", body < self.config.alignment_angle, time):
                self.active["bad_alignment"] = True
            if top:
                reasons = []
                if not self.active["bottom"]:
                    reasons.append("Required bottom-angle evidence not observed.")
                if self.active["bad_alignment"]:
                    reasons.append("Body-line angle fell below the configured threshold.")
                self.complete(time, "rejected" if reasons else "accepted", reasons or ["Observable rubric satisfied."])
                self.phase = "top"
                self.holds.clear()

    def finish(self):
        if not self.closed:
            if self.active is not None:
                self.complete(self.previous, "unable_to_assess", ["Video ended before return to top was verified."])
            if self.open_gap is not None:
                self.uncertainty.append({"start_s": self.open_gap, "end_s": self.previous})
                self.open_gap = None
            self.closed = True
        return {"mode": self.mode, "config": asdict(self.config),
                "counts": {s: sum(a["status"] == s for a in self.attempts)
                           for s in ("accepted", "rejected", "unable_to_assess")},
                "attempts": list(self.attempts), "uncertainty_intervals": list(self.uncertainty),
                "note": "Only top-anchored attempts are segmented; missing evidence can hide additional reps."}
