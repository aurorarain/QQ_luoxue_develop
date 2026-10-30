import pathlib
import time
import types
import unittest
from unittest.mock import patch

from test_boundaries import features, Event
from astrbot.api.message_components import Image


def build(index, state=None, choose=None):
    f = features.Features.__new__(features.Features)
    f.index = index
    f.library = pathlib.Path('/not-used')
    f.s = types.SimpleNamespace(state=state if state is not None else {}, save=lambda: None)
    f.roster_cache = []
    f.choose_meme = choose or (lambda *a, **k: None)
    return f


class MemeInstructions(unittest.TestCase):
    def test_prompt_is_compact_instead_of_dumping_every_file(self):
        index = [{'sha': 'a%02d' % i, 'file': '开心/肥鱼_%04d_笑.gif' % i, 'category': '开心',
                  'scope': 'public', 'used': 0} for i in range(60)]
        f = build(index)
        text = f.meme_instructions(False)
        self.assertLess(len(text), 1200)
        self.assertIn('开心 60张', text)

    def test_group_never_advertises_private_only_categories(self):
        index = [{'sha': 'x1', 'file': '喜欢/亲亲.gif', 'category': '喜欢', 'scope': 'private'},
                 {'sha': 'x2', 'file': '开心/笑.gif', 'category': '开心', 'scope': 'public'}]
        f = build(index)
        group_inventory = f.meme_instructions(False).split('可用素材：', 1)[1]
        self.assertIn('开心', group_inventory)
        self.assertNotIn('喜欢', group_inventory)
        private_inventory = f.meme_instructions(True).split('可用素材：', 1)[1]
        self.assertIn('喜欢', private_inventory)

    def test_last_sent_sticker_is_reported_back(self):
        index = [{'sha': 'x2', 'file': '开心/肥鱼_0102_点头.gif', 'category': '开心', 'scope': 'public'}]
        state = {}
        f = build(index, state=state, choose=lambda *a, **k: pathlib.Path('/not-used/肥鱼_0102_点头.gif'))
        f.reply_chain('好耶[表情:开心]', False, 'g')
        self.assertEqual(f.last_meme(False)['meaning'], '肥鱼_0102_点头')
        self.assertIn('你上一次刚发过', f.meme_instructions(False))


class MemeTrigger(unittest.TestCase):
    def sticker(self):
        return pathlib.Path('/not-used/肥鱼_0001_笑.gif')

    def test_strong_emotion_may_send_sooner(self):
        f = build([], state={}, choose=lambda *a, **k: self.sticker())
        chain = f.reply_chain('哼，才不是呢[表情:傲娇]', False, 'g')
        self.assertTrue(any(isinstance(c, Image) for c in chain))

    def test_calm_line_still_needs_a_second_turn(self):
        f = build([], state={}, choose=lambda *a, **k: self.sticker())
        first = f.reply_chain('今天天气还行[表情:回应]', False, 'g')
        self.assertFalse(any(isinstance(c, Image) for c in first))
        second = f.reply_chain('吃了吗[表情:回应]', False, 'g')
        self.assertTrue(any(isinstance(c, Image) for c in second))

    def test_cooldown_blocks_back_to_back_stickers(self):
        f = build([], state={}, choose=lambda *a, **k: self.sticker())
        f.reply_chain('哼[表情:傲娇]', False, 'g')
        again = f.reply_chain('哼[表情:傲娇]', False, 'g')
        self.assertFalse(any(isinstance(c, Image) for c in again))

    def test_marker_is_stripped_from_text(self):
        f = build([], state={}, choose=lambda *a, **k: self.sticker())
        chain = f.reply_chain('好耶[表情:开心]', False, 'g')
        text = ''.join(getattr(c, 'text', '') or '' for c in chain)
        self.assertNotIn('[表情:', text)
