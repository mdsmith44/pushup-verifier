"""HRP sequence verifier for manually reviewed or future model observations.

This module does not infer ground contact or bilateral arm position from angles.
"""

import math


class HRPVerifier:
    def __init__(self, mode="temporal", persistence=0.1, min_confidence=0.6, max_gap=0.25):
        if mode not in {"immediate", "temporal"}:
            raise ValueError("Unknown mode")
        if not all(math.isfinite(v) for v in (persistence, min_confidence, max_gap)):
            raise ValueError("Settings must be finite")
        if persistence < 0 or not 0 <= min_confidence <= 1 or max_gap <= 0:
            raise ValueError("Invalid settings")
        self.mode = mode
        self.persistence = persistence if mode == "temporal" else 0
        self.min_confidence, self.max_gap = min_confidence, max_gap
        self.phase = "await_prone"
        self.previous = None
        self.candidate = None
        self.since = 0
        self.active = None
        self.attempts = []
        self.gaps = []
        self.closed = False

    def complete(self, time, reason=None, interrupted=False):
        reasons = list(self.active["faults"])
        if reason:
            reasons.append(reason)
        status = "unable_to_assess" if interrupted else "rejected" if reasons else "unable_to_assess" if self.active["unknown"] else "accepted"
        if self.active["unknown"] and not interrupted:
            reasons.append("One or more technique requirements were not assessed.")
        self.attempts.append({"start_s": self.active["start_s"], "end_s": time,
                              "status": status, "reasons": reasons or ["Sequence and supplied technique observations passed."]})
        self.active = None

    def update(self, time, pose, technique, confidence):
        if self.closed:
            raise ValueError("Verifier is finalized")
        if not math.isfinite(time) or time < 0 or (self.previous is not None and time <= self.previous):
            raise ValueError("Time must be finite, nonnegative, and increasing")
        if pose not in {"prone", "up", "t", "transition", "unknown"}:
            raise ValueError("Invalid pose")
        if technique not in {"pass", "fail", "unknown"}:
            raise ValueError("Invalid technique assessment")
        if not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ValueError("Invalid confidence")
        gap = self.previous is not None and time - self.previous > self.max_gap + 1e-9
        old_time = self.previous
        self.previous = time
        if gap or pose == "unknown" or confidence < self.min_confidence:
            if self.active:
                self.complete(time, "Missing phase evidence; reacquire the prone start.", interrupted=True)
            self.gaps.append({"start_s": old_time if gap else time, "end_s": time})
            self.phase, self.candidate = "await_prone", None
            return
        # Technique observations apply throughout motion and rest, not just
        # the stable phases. They must come from independent visual review.
        if self.active:
            if technique == "fail" and "Technique violation observed." not in self.active["faults"]:
                self.active["faults"].append("Technique violation observed.")
            self.active["unknown"] |= technique == "unknown"
        if pose != self.candidate:
            self.candidate, self.since = pose, time
        if time - self.since + 1e-9 < self.persistence:
            return
        if self.phase == "await_prone":
            if pose == "prone":
                self.phase = "ready"
                self.start_technique = technique
            return
        if self.phase == "ready":
            if pose == "prone":
                self.start_technique = technique
                return
            self.active = {"start_s": self.since, "faults": [],
                           "unknown": "unknown" in {technique, self.start_technique}}
            if "fail" in {technique, self.start_technique}:
                self.active["faults"].append("Technique violation observed.")
            self.phase = "await_up"
        if pose == "transition":
            return
        if self.phase == "await_up":
            if pose == "up":
                self.phase = "await_ground"
            elif pose in {"prone", "t"}:
                self.complete(time, "Full-extension up phase was not observed before return/release.")
                self.phase = "await_prone"
        elif self.phase == "await_ground":
            if pose == "prone":
                self.phase = "await_t"
            elif pose == "t":
                self.complete(time, "Return to ground was not observed before T-position.")
                self.phase = "await_prone"
        elif self.phase == "await_t":
            if pose == "t":
                self.phase = "await_hands"
            elif pose == "up":
                self.complete(time, "Next ascent began without the T-position and hand return.")
                self.phase = "await_prone"
        elif self.phase == "await_hands":
            if pose == "prone":
                self.complete(time)
                self.phase, self.start_technique = "ready", technique
            elif pose == "up":
                self.complete(time, "Hands-back prone phase was not observed before next ascent.")
                self.phase = "await_prone"

    def finish(self):
        if not self.closed:
            if self.active:
                self.complete(self.previous, "Recording ended before the HRP sequence completed.", interrupted=True)
            self.closed = True
        return {"standard": "HRP arm extension; user-supplied four-movement specification",
                "mode": self.mode, "settings": {"persistence": self.persistence, "min_confidence": self.min_confidence, "max_gap": self.max_gap},
                "scope": "Observation replay only; technique pass must be supplied by review, not inferred from legacy elbow angles.",
                "counts": {s: sum(a["status"] == s for a in self.attempts) for s in ("accepted", "rejected", "unable_to_assess")},
                "attempts": self.attempts, "evidence_gaps": self.gaps,
                "limitations": ["No automatic technique or contact classifier", "No official event-termination logic", "Unobserved phases may conceal additional reps"]}
