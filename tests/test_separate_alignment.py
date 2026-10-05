import unittest
from pushup.engine import Verifier, Config


class SeparateAlignmentTests(unittest.TestCase):
    def run_rows(self, rows, mode='immediate'):
        v=Verifier(Config(smoothing_tau=0), mode, separate_alignment=True)
        for i,(e,b,c) in enumerate(rows):
            v.update(i*.05,e,b,c)
        return v.finish()

    def test_missing_alignment_preserves_completion(self):
        r=self.run_rows([(170,175,1),(85,None,1),(170,175,1)])
        self.assertEqual(r['completed_movements'],1)
        self.assertEqual(r['counts']['unable_to_assess'],1)
        self.assertEqual(r['counts']['accepted'],0)

    def test_missing_arm_interrupts(self):
        r=self.run_rows([(170,175,1),(85,175,1),(85,175,.2),(170,175,1)])
        self.assertEqual(r['completed_movements'],0)
        self.assertFalse(r['attempts'][0]['completed'])

    def test_no_initial_top_does_not_invent_attempt(self):
        r=self.run_rows([(85,None,1),(170,175,1)])
        self.assertEqual(r['attempts'],[])

    def test_reliable_bad_alignment_still_rejected(self):
        r=self.run_rows([(170,175,1),(85,140,1),(170,175,1)])
        self.assertEqual(r['counts']['rejected'],1)
        self.assertEqual(r['completed_movements'],1)

    def test_missing_during_departure_persistence_is_retained(self):
        r=self.run_rows([(170,175,1)]*4+[(85,None,1)]+[(85,175,1)]*4+[(170,175,1)]*4,'temporal')
        self.assertEqual(r['counts']['unable_to_assess'],1)
        self.assertEqual(r['completed_movements'],1)

    def test_unknown_body_does_not_bridge_alignment_hold(self):
        r=self.run_rows([(170,175,1)]*4+[(85,175,1)]*4+[(85,140,1),(85,None,1),(85,140,1)]+[(170,175,1)]*4,'temporal')
        self.assertNotIn('Body-line angle fell below the configured threshold.',r['attempts'][0]['reasons'])

    def test_gap_does_not_contaminate_next_rep(self):
        r=self.run_rows([(170,175,1),(85,None,1),(170,175,1),(85,175,1),(170,175,1)])
        self.assertEqual(r['counts']['accepted'],1)
        self.assertEqual(r['counts']['unable_to_assess'],1)

    def test_truncated_attempt_not_completed(self):
        r=self.run_rows([(170,175,1),(85,None,1)])
        self.assertEqual(r['completed_movements'],0)
