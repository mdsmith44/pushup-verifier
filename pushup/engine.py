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
    def __init__(self, config=None, mode="temporal", separate_alignment=False, partial_start=False):
        if mode not in {"immediate", "temporal"}:
            raise ValueError("Unknown mode")
        self.config = config or Config()
        self.mode = mode
        self.separate_alignment = separate_alignment
        self.partial_start = partial_start
        self.startup_available = partial_start
        self.startup_peak = None
        self.alignment_gaps = []
        self.pending_alignment_gap = False
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

    def complete(self, time, status, reasons, completed=False):
        self.attempts.append({"start_s": self.active["start_s"], "end_s": time,
                              "status": status, "reasons": reasons})
        if self.separate_alignment or self.partial_start:
            self.attempts[-1]['completed'] = completed
        if self.partial_start:
            self.attempts[-1]['start_observed'] = not self.active.get('partial_start', False)
        self.active = None

    def interrupt(self, time, start):
        self.startup_available = False
        if self.active is not None:
            self.complete(time, "unable_to_assess", ["Required pose evidence missing."])
        if self.open_gap is None:
            self.open_gap = start
        self.phase, self.filtered = "await_top", None
        self.holds.clear()
        self.pending_alignment_gap = False

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
        if elbow is None or (body is None and not self.separate_alignment) or confidence < self.config.min_confidence:
            self.interrupt(time, time)
            return
        if body is None:
            self.alignment_gaps.append(time)
            self.holds.pop('alignment', None)
        if self.open_gap is not None:
            self.uncertainty.append({"start_s": self.open_gap, "end_s": time})
            self.open_gap = None
        tau = self.config.smoothing_tau if self.mode == "temporal" else 0
        if self.filtered is None or tau == 0:
            self.filtered = (elbow, body)
        else:
            alpha = 1 - math.exp(-delta / tau)
            self.filtered = tuple(None if new is None else new if old is None else old + alpha * (new - old) for old, new in zip(self.filtered, (elbow, body)))
        elbow, body = self.filtered
        if self.startup_available:
            self.startup_peak = max(elbow, self.startup_peak if self.startup_peak is not None else elbow)
        top = self.held("top", elbow >= self.config.top_angle, time)
        departure = self.held("departure", elbow <= self.config.departure_angle, time)
        if self.phase == 'top':
            if 'departure' not in self.holds:
                self.pending_alignment_gap = False
            elif body is None:
                self.pending_alignment_gap = True

        if self.phase == "await_top":
            if top:
                self.phase = "top"
                self.startup_available = False
                return
            if self.startup_available and departure and self.startup_peak - elbow >= 10:
                self.active = {"start_s": time, "bottom": False, "bad_alignment": False,
                               "alignment_missing": body is None, "partial_start": True}
                self.phase = 'attempt'
                self.startup_available = False
            else:
                return
        if self.phase == "top" and departure:
            self.active = {"start_s": self.holds["departure"], "bottom": False, "bad_alignment": False, "alignment_missing": self.pending_alignment_gap}
            self.phase = "attempt"
        if self.phase == "attempt":
            if body is None:
                self.active['alignment_missing'] = True
            if self.held("bottom", elbow <= self.config.bottom_angle, time):
                self.active["bottom"] = True
            if self.held("alignment", body is not None and body < self.config.alignment_angle, time):
                self.active["bad_alignment"] = True
            if top:
                reasons = []
                if not self.active["bottom"]:
                    reasons.append("Required bottom-angle evidence not observed.")
                if self.active["bad_alignment"]:
                    reasons.append("Body-line angle fell below the configured threshold.")
                status = "rejected" if reasons else "accepted"
                if self.active['alignment_missing']:
                    status = 'unable_to_assess'
                    reasons.append('Movement completed; alignment evidence missing during attempt.')
                if self.active.get('partial_start', False):
                    status = 'unable_to_assess'
                    reasons.append('Return to top observed, but initial top was not verified (partial start).')
                self.complete(time, status, reasons or ["Observable rubric satisfied."], completed=True)
                self.phase = "top"
                self.holds.clear()
                self.pending_alignment_gap = False

    def finish(self):
        if not self.closed:
            if self.active is not None:
                self.complete(self.previous, "unable_to_assess", ["Video ended before return to top was verified."])
            if self.open_gap is not None:
                self.uncertainty.append({"start_s": self.open_gap, "end_s": self.previous})
                self.open_gap = None
            self.closed = True
        report = {"mode": self.mode, "config": asdict(self.config),
                "counts": {s: sum(a["status"] == s for a in self.attempts)
                           for s in ("accepted", "rejected", "unable_to_assess")},
                "attempts": list(self.attempts), "uncertainty_intervals": list(self.uncertainty),
                "note": "Only top-anchored attempts are segmented; missing evidence can hide additional reps."}
        if self.separate_alignment:
            report['evidence_policy'] = 'separate_alignment'
            report['completed_movements'] = sum(a['completed'] for a in self.attempts)
            report['alignment_uncertain_timestamps'] = list(self.alignment_gaps)
        if self.partial_start:
            report['startup_policy'] = 'partial_start_after_10_degree_descent'
            report['completed_movements'] = sum(a['completed'] and a['start_observed'] for a in self.attempts)
            report['partial_start_returns'] = sum(a['completed'] and not a['start_observed'] for a in self.attempts)
            report['note'] = 'Partial-start returns are reported separately from fully top-anchored completed movements. Missing evidence can hide additional reps.'
        return report
