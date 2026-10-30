import types
import unittest

import test_boundaries  # noqa: F401
from test_boundaries import main, features


def social(state=None):
    s = main.Social.__new__(main.Social)
    s.state = state if state is not None else {}
    s.save = lambda: None
    return s


class NoDoubleCounting(unittest.TestCase):
    def test_same_message_from_two_channels_is_recorded_once(self):
        s = social()
        s.add('group_observed', '90001', '画的不错')
        s.add('group', '90001', '画的不错')
        self.assertEqual(len(s.state.get('group_observed') or []), 1)
        self.assertEqual(len(s.state.get('group') or []), 0)

    def test_different_text_or_old_message_is_not_merged(self):
        s = social()
        s.add('group_observed', '90001', '画的不错')
        s.add('group', '90001', '画得不错')      # different wording
        s.add('group_observed', '90002', '画的不错')  # different speaker
        self.assertEqual(len(s.state['group_observed']), 2)
        self.assertEqual(len(s.state.get('group') or []), 1)

    def test_group_memory_collapses_duplicate_rows(self):
        s = social({'group_observed': [{'time': 100, 'sender': '90001', 'text': '画的不错'}],
                    'group': [{'time': 101, 'sender': '90001', 'text': '画的不错'}]})
        memory = s.group_memory('画的不错')
        self.assertEqual(len(memory), 1)
        self.assertEqual(memory[0]['text'], '画的不错')

    def test_group_memory_keeps_genuinely_repeated_lines_apart(self):
        s = social({'group_observed': [{'time': 100, 'sender': '90001', 'text': '哈哈哈'}],
                    'group': [{'time': 100 + 600, 'sender': '90001', 'text': '哈哈哈'}]})
        self.assertEqual(len(s.group_memory('哈哈哈')), 2)


class DrawingHonesty(unittest.TestCase):
    def test_context_forbids_claiming_more_than_one_look(self):
        f = features.Features.__new__(features.Features)
        f.s = types.SimpleNamespace(state={}, save=lambda: None)
        self.assertIn('不要说看了两遍', f.drawing_context(True))
