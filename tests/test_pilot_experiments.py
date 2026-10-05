import unittest
from examples.pilot_experiments import replay
from pushup.engine import Config


def rows(values):
    return [dict(timestamp=i/30, elbow_angle=angle, body_angle=175, confidence=confidence)
            for i, (angle, confidence) in enumerate(values)]


class GapExperimentTests(unittest.TestCase):
    def test_isolated_gap_preserves_attempt_but_marks_conditional_acceptance(self):
        result = replay(rows([(170,1),(120,1),(110,.2),(85,1),(170,1)]), Config(), 'immediate', True)
        self.assertEqual(result['counts']['accepted'], 1)
        self.assertTrue(result['attempts'][0]['contains_tolerated_gap'])

    def test_missing_bottom_is_not_invented(self):
        result = replay(rows([(170,1),(120,1),(80,.2),(120,1),(170,1)]), Config(), 'immediate', True)
        self.assertEqual(result['counts']['rejected'], 1)

    def test_two_bad_frames_still_interrupt(self):
        result = replay(rows([(170,1),(120,1),(80,.2),(80,.2),(170,1)]), Config(), 'immediate', True)
        self.assertEqual(result['counts']['unable_to_assess'], 1)
        self.assertEqual(result['tolerated_gaps'], [])

    def test_trailing_bad_frame_is_not_skipped(self):
        result = replay(rows([(170,1),(85,1),(80,.2)]), Config(), 'immediate', True)
        self.assertEqual(result['counts']['unable_to_assess'], 1)

    def test_sparse_neighbors_are_not_bridged(self):
        observations = rows([(170,1),(120,1),(80,.2),(170,1)])
        observations[-1]['timestamp'] = .2
        result = replay(observations, Config(), 'immediate', True)
        self.assertEqual(result['tolerated_gaps'], [])

    def test_temporal_hold_does_not_cross_gap(self):
        observations = rows([(170,1)]*8+[(85,1),(85,1),(85,.2),(85,1)]+[(170,1)]*12)
        result = replay(observations, Config(smoothing_tau=0), 'temporal', True)
        self.assertEqual(result['counts']['accepted'], 0)
