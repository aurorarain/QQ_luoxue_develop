# All scenarios below are synthetic.
import unittest
from unittest.mock import Mock

from test_boundaries import features
from luoxue_social.presentation import location


class Presentation(unittest.TestCase):
    def test_activity_selects_canonical_motion_and_location(self):
        for text, action, spot, mode, room, motion in [
            ('在厨房煮东西', 'eat', 'sofa', 'awake', 'kitchen', 'cook'),
            ('在电脑上写日记', 'type', 'desk', 'awake', 'study', 'write'),
            ('在花园浇水', 'phone', 'window', 'awake', 'garden', 'water'),
            ('打两把游戏', 'type', 'desk', 'awake', 'gaming', 'game'),
            ('窝在沙发听歌', 'read', 'sofa', 'awake', 'living', 'listen'),
            ('午睡中', 'lie', 'bed', 'nap', 'bedroom', 'sleep'),
        ]:
            with self.subTest(text=text):
                result = location(text, action, spot, mode)
                self.assertEqual((result['room'], result['motion']), (room, motion))
        self.assertIsNone(location('在外面', 'away', 'away', 'awake', True)['room'])

    def test_repeated_reads_do_not_advance_the_room(self):
        f = features.Features.__new__(features.Features)
        f._build_room_state = Mock(return_value={'room': 'study', 'motion': 'read'})
        self.assertIs(f.room_state(), f.room_state())
        f._build_room_state.assert_called_once()
