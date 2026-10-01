import unittest
from pushup.hrp import HRPVerifier


def run(poses, mode="temporal", bad=None, unknown=None):
    checker = HRPVerifier(mode)
    tick = 0
    for i, pose in enumerate(poses):
        for _ in range(4):
            checker.update(tick / 20, pose, "fail" if i == bad else "unknown" if i == unknown else "pass", 1)
            tick += 1
    return checker.finish()


class HRPTests(unittest.TestCase):
    def test_complete(self):
        for mode in ("immediate", "temporal"):
            self.assertEqual(run(["prone", "up", "prone", "t", "prone"], mode)["counts"]["accepted"], 1)

    def test_not_counted_at_top(self):
        result = run(["prone", "up"])
        self.assertEqual(result["counts"]["accepted"], 0)
        self.assertEqual(result["counts"]["unable_to_assess"], 1)

    def test_no_release(self):
        self.assertEqual(run(["prone", "up", "prone", "up"])["counts"]["rejected"], 1)

    def test_no_ground(self):
        self.assertEqual(run(["prone", "up", "t"])["counts"]["rejected"], 1)

    def test_no_up(self):
        self.assertEqual(run(["prone", "t"])["counts"]["rejected"], 1)

    def test_hands_return_required(self):
        self.assertEqual(run(["prone", "up", "prone", "t"])["counts"]["accepted"], 0)

    def test_two_reps(self):
        self.assertEqual(run(["prone", "up", "prone", "t", "prone", "up", "prone", "t", "prone"])["counts"]["accepted"], 2)

    def test_bad_rest_rejected(self):
        self.assertEqual(run(["prone", "up", "up", "prone", "t", "prone"], bad=2)["counts"]["rejected"], 1)

    def test_unknown_technique_not_accepted(self):
        self.assertEqual(run(["prone", "up", "prone", "t", "prone"], unknown=3)["counts"]["unable_to_assess"], 1)

    def test_occlusion_not_bridge(self):
        result = run(["prone", "up", "unknown", "prone", "t", "prone"])
        self.assertEqual(result["counts"]["accepted"], 0)

    def test_static_start(self):
        self.assertEqual(sum(run(["prone", "prone"])["counts"].values()), 0)

    def test_finish_idempotent_and_invalid_time(self):
        checker = HRPVerifier()
        checker.update(0, "prone", "pass", 1)
        with self.assertRaises(ValueError):
            checker.update(0, "up", "pass", 1)
        self.assertEqual(checker.finish(), checker.finish())


if __name__ == "__main__":
    unittest.main()
