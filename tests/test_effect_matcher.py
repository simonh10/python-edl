# -*- coding: utf-8 -*-

import unittest
import re
from edl import EffectMatcher, List, Event, Effect


class EffectMatcherTestCase(unittest.TestCase):
    """tests the edl.edl.EffectMatcher class
    """

    def setup(self):
        """set up the tests
        """
        pass

    def test_EffectMatcher_regex_is_working_properly(self):
        """testing if the EffectMatcher.regex is working properly
        """
        test_line = 'EFFECTS NAME IS Constant Power'
        e = EffectMatcher()

        m = re.search(e.regex, test_line)

        self.assertIsNotNone(m)

        self.assertEqual(
            'Constant Power',
            m.group(2).strip()
        )

    def test_EffectMatcher_apply_is_working_properly(self):
        """testing if the EffectMatcher.apply() is working properly
        """
        ed_list = List('24')
        event = Event({})
        event.transition = Effect()
        ed_list.append(event)

        e = EffectMatcher()

        test_line = 'EFFECTS NAME IS Constant Power'
        e.apply(ed_list, test_line)

        self.assertEqual(
            'Constant Power',
            event.transition.effect
        )

        test_line = 'EFFECTS NAME IS CROSS DISSOLVE'
        e.apply(ed_list, test_line)

        self.assertEqual(
            'CROSS DISSOLVE',
            event.transition.effect
        )
