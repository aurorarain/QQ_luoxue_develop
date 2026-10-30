import datetime as dt
import types
import unittest

import test_boundaries  # noqa: F401  (installs astrbot stubs)
from luoxue_social import life
from luoxue_social.rhythm import TZ


def social(state=None):
    return types.SimpleNamespace(state=state if state is not None else {}, save=lambda: None)


class LifeDay(unittest.TestCase):
    def test_slots_follow_the_clock(self):
        for hour, expected in ((2, '深夜'), (7, '清晨'), (10, '上午'), (13, '午后'),
                               (17, '黄昏'), (20, '夜里'), (23, '深夜')):
            self.assertEqual(life.slot_of(hour)[0], expected, hour)

    def test_one_activity_per_slot_per_day(self):
        s = social()
        day = dt.datetime(2026, 10, 30, 10, 0, tzinfo=TZ)
        slot, action = life.advance(s, day)
        self.assertEqual(slot, '上午')
        self.assertTrue(action)
        _, again = life.advance(s, day.replace(hour=11))
        self.assertEqual(again, action)
        life.advance(s, day.replace(hour=14))
        self.assertEqual(sorted(s.state['life']['slots']), ['上午', '午后'])

    def test_context_marks_role_play_and_uses_real_material_only(self):
        s = social({'discoveries': [{'title': '某公开话题标题'}]})
        life.advance(s, dt.datetime(2026, 10, 30, 10, 0, tzinfo=TZ))
        text = life.context(s, dt.datetime(2026, 10, 30, 11, 0, tzinfo=TZ))
        self.assertIn('角色演绎', text)
        self.assertIn('不能声称真的做过', text)
        self.assertIn('某公开话题标题', text)

    def test_day_rollover_resets(self):
        s = social()
        life.advance(s, dt.datetime(2026, 10, 30, 10, 0, tzinfo=TZ))
        self.assertEqual(life.context(s, dt.datetime(2026, 10, 31, 10, 0, tzinfo=TZ)), '')
        life.advance(s, dt.datetime(2026, 10, 31, 10, 0, tzinfo=TZ))
        self.assertEqual(s.state['life']['day'], '2026-10-31')

    def test_activities_are_stable_per_day_but_vary_across_days(self):
        s1, s2 = social(), social()
        day1 = dt.datetime(2026, 10, 30, 10, 0, tzinfo=TZ)
        day2 = dt.datetime(2026, 10, 31, 10, 0, tzinfo=TZ)
        _, a1 = life.advance(s1, day1)
        _, a1_again = life.advance(social(), day1)
        self.assertEqual(a1, a1_again)
        _, a2 = life.advance(s2, day2)
        self.assertTrue(a2)

    def test_current_activity_is_not_repeated(self):
        s = social()
        life.advance(s, dt.datetime(2026, 10, 30, 10, 0, tzinfo=TZ))
        text = life.context(s, dt.datetime(2026, 10, 30, 10, 30, tzinfo=TZ))
        self.assertEqual(text.count('此刻'), 1)
        life.advance(s, dt.datetime(2026, 10, 30, 14, 0, tzinfo=TZ))
        text = life.context(s, dt.datetime(2026, 10, 30, 15, 0, tzinfo=TZ))
        self.assertIn('上午', text)
        self.assertIn('此刻午后', text)
        self.assertEqual(text.count('此刻'), 1)

    def test_no_discovery_means_no_fake_reading(self):
        s = social()
        life.advance(s, dt.datetime(2026, 10, 30, 10, 0, tzinfo=TZ))
        self.assertNotIn('读到过', life.context(s, dt.datetime(2026, 10, 30, 10, 5, tzinfo=TZ)))
