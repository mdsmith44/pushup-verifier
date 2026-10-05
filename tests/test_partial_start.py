import unittest
from pushup.engine import Verifier


class PartialStartTests(unittest.TestCase):
    def replay(self, values):
        v=Verifier(mode='immediate',partial_start=True)
        for i,(angle,confidence) in enumerate(values):
            v.update(i*.05,angle,175,confidence)
        return v.finish()

    def test_descent_return_unassessable_not_full_rep(self):
        r=self.replay([(135,1),(120,1),(85,1),(170,1)])
        self.assertEqual(r['partial_start_returns'],1)
        self.assertEqual(r['completed_movements'],0)
        self.assertEqual(r['counts']['accepted'],0)

    def test_stationary_bent_then_up_not_counted(self):
        r=self.replay([(85,1)]*5+[(170,1)])
        self.assertEqual(r['attempts'],[])

    def test_does_not_rearm_after_gap(self):
        r=self.replay([(135,1),(120,0),(135,1),(100,1),(170,1)])
        self.assertEqual(r['attempts'],[])

    def test_following_complete_rep_can_be_valid(self):
        r=self.replay([(135,1),(120,1),(85,1),(170,1),(85,1),(170,1)])
        self.assertEqual(r['partial_start_returns'],1)
        self.assertEqual(r['completed_movements'],1)
        self.assertEqual(r['counts']['accepted'],1)

    def test_truncated_partial_is_not_return(self):
        r=self.replay([(135,1),(100,1)])
        self.assertEqual(r['partial_start_returns'],0)
        self.assertFalse(r['attempts'][0]['completed'])
