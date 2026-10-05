import unittest
from examples.ankle_guard import discontinuity


class AnkleGuardTests(unittest.TestCase):
    def test_translation_is_not_relative_jump(self):
        a=dict(timestamp=0,hip_x=0,hip_y=0,ankle_x=100,ankle_y=0)
        b=dict(timestamp=.033,hip_x=50,hip_y=20,ankle_x=150,ankle_y=20)
        self.assertEqual(discontinuity(a,b),(0,0))

    def test_ankle_jump_is_flagged(self):
        a=dict(timestamp=0,hip_x=0,hip_y=0,ankle_x=100,ankle_y=0)
        b=dict(timestamp=.033,hip_x=0,hip_y=0,ankle_x=70,ankle_y=0)
        self.assertGreater(max(discontinuity(a,b)),3)

    def test_missing_coordinates_not_comparable(self):
        self.assertIsNone(discontinuity(dict(timestamp=0),dict(timestamp=.033)))
