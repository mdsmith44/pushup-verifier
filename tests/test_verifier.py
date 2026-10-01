import unittest
from pushup.engine import Config, Verifier
from pushup.geometry import angle


def replay(segments, mode="temporal"):
    verifier = Verifier(mode=mode)
    tick = 0
    for elbow, body, confidence, count in segments:
        for _ in range(count):
            verifier.update(tick / 20, elbow, body, confidence)
            tick += 1
    return verifier.finish()


TOP = (175, 175, 0.95, 10)
BOTTOM = (85, 175, 0.95, 10)


class VerifierTests(unittest.TestCase):
    def test_pilot_top_threshold(self):
        for mode in ("immediate", "temporal"):
            result = replay([(147, 175, 0.95, 20), BOTTOM, (147, 175, 0.95, 20)], mode)
            self.assertEqual(result["counts"]["accepted"], 1)

    def test_top_departure_gap_prevents_attempt(self):
        for mode in ("immediate", "temporal"):
            result = replay([(147, 175, 0.95, 20), (140, 175, 0.95, 20), (147, 175, 0.95, 20)], mode)
            self.assertEqual(sum(result["counts"].values()), 0)

    def test_valid_both_methods(self):
        for mode in ("immediate", "temporal"):
            self.assertEqual(replay([TOP, BOTTOM, TOP], mode)["counts"]["accepted"], 1)

    def test_multiple_reps(self):
        self.assertEqual(replay([TOP, BOTTOM, TOP, BOTTOM, TOP])["counts"]["accepted"], 2)

    def test_depth_boundary_immediate(self):
        for depth, expected in [(89.9, "accepted"), (90, "accepted"), (90.1, "rejected"), (95, "rejected")]:
            with self.subTest(depth=depth):
                result = replay([TOP, (depth, 175, 0.95, 10), TOP], "immediate")
                self.assertEqual(result["counts"][expected], 1)

    def test_above_ninety_rejected_temporal(self):
        self.assertEqual(replay([TOP, (95, 175, 0.95, 10), TOP])["counts"]["rejected"], 1)

    def test_shallow_rejected(self):
        result = replay([TOP, (120, 175, 0.95, 10), TOP])
        self.assertEqual(result["counts"]["rejected"], 1)

    def test_alignment_rejected(self):
        self.assertEqual(replay([TOP, (85, 130, 0.95, 10), TOP])["counts"]["rejected"], 1)

    def test_visibility_interrupts_and_rearms(self):
        result = replay([TOP, BOTTOM, (None, None, 0, 2), TOP, BOTTOM, TOP])
        self.assertEqual(result["counts"], {"accepted": 1, "rejected": 0, "unable_to_assess": 1})
        self.assertEqual(len(result["uncertainty_intervals"]), 1)

    def test_low_confidence(self):
        self.assertEqual(replay([TOP, BOTTOM, (85, 175, 0.2, 1), TOP])["counts"]["unable_to_assess"], 1)

    def test_truncated_attempt(self):
        self.assertEqual(replay([TOP, BOTTOM])["counts"]["unable_to_assess"], 1)

    def test_no_initial_top_no_fabricated_rep(self):
        self.assertEqual(sum(replay([BOTTOM, TOP])["counts"].values()), 0)

    def test_stationary_top(self):
        self.assertEqual(sum(replay([TOP, TOP])["counts"].values()), 0)

    def test_one_frame_glitch(self):
        segments = [TOP, (85, 175, 0.95, 1), TOP]
        self.assertEqual(replay(segments, "immediate")["counts"]["accepted"], 1)
        self.assertEqual(sum(replay(segments, "temporal")["counts"].values()), 0)

    def test_large_gap(self):
        verifier = Verifier(mode="immediate")
        verifier.update(0, 175, 175, 1)
        verifier.update(0.1, 85, 175, 1)
        verifier.update(1, 175, 175, 1)
        self.assertEqual(verifier.finish()["counts"]["unable_to_assess"], 1)

    def test_invalid_values(self):
        for values in [(float("nan"), 175, 175, 1), (0, 181, 175, 1), (0, 175, 175, 2)]:
            with self.assertRaises(ValueError):
                Verifier().update(*values)
        with self.assertRaises(ValueError):
            Config(bottom_angle=170)

    def test_finalize_idempotent(self):
        verifier = Verifier(mode="immediate")
        verifier.update(0, 175, 175, 1)
        verifier.update(0.1, 85, 175, 1)
        self.assertEqual(verifier.finish(), verifier.finish())
        with self.assertRaises(ValueError):
            verifier.update(0.2, 175, 175, 1)

    def test_geometry(self):
        self.assertAlmostEqual(angle((0, 1), (0, 0), (1, 0)), 90)
        self.assertAlmostEqual(angle((-1, 0), (0, 0), (1, 0)), 180)
        with self.assertRaises(ValueError):
            angle((0, 0), (0, 0), (1, 0))


if __name__ == "__main__":
    unittest.main()
