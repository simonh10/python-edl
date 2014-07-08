# -*- coding: utf-8 -*-

import unittest
from edl import Timewarp


class TimeWarpTestCase(unittest.TestCase):
    """tests the edl.edl.Timewarp class
    """

    def setup(self):
        """set up the tests
        """
        pass

    def test_to_string_is_working_properly(self):
        """testing if the TitleMatcher.to_string is working properly
        """
        expected_output = \
            'M2   AX       -25.0                      00:00:00:00 '

        fps = '24'
        tw = Timewarp('AX', '-25.0', '00:00:00:00', fps)

        self.assertEqual(
            expected_output,
            tw.to_string()
        )
