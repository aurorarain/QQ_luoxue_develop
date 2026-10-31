import pathlib
import types
import unittest

import test_boundaries  # noqa: F401
from test_boundaries import features
from astrbot.api.message_components import At


def build(roster):
    f = features.Features.__new__(features.Features)
    f.roster_cache = roster
    f.s = types.SimpleNamespace(state={}, save=lambda: None)
    f.library = pathlib.Path('/not-used')
    f.index = []
    f.index_path = pathlib.Path('/not-used.json')
    f.choose_meme = lambda *a, **k: None
    return f


ROSTER = [{'qq': '90001', 'name': '西洲'}, {'qq': '90002', 'name': '昔泠'}]


class MultiMention(unittest.TestCase):
    def test_two_markers_produce_two_real_mentions(self):
        chain = build(ROSTER).reply_chain('行：[at:90001] 出来，[at:90002] 也来。', False, 'g')
        mentions = [c for c in chain if isinstance(c, At)]
        self.assertEqual([str(m.qq) for m in mentions], ['90001', '90002'])

    def test_bare_name_is_not_a_mention_but_at_name_is(self):
        f = build(ROSTER)
        plain = f.reply_chain('点名就点名：西洲，出来。', False, 'g')
        self.assertFalse(any(isinstance(c, At) for c in plain))
        converted = f.reply_chain('@西洲 出来', False, 'g')
        self.assertEqual([str(c.qq) for c in converted if isinstance(c, At)], ['90001'])

    def test_unknown_ids_are_dropped_and_cap_is_three(self):
        chain = build(ROSTER).reply_chain(
            '[at:90001][at:90002][at:99999][at:90001][at:90002]', False, 'g')
        mentions = [c for c in chain if isinstance(c, At)]
        self.assertLessEqual(len(mentions), 3)
        self.assertTrue(all(str(m.qq) in {'90001', '90002'} for m in mentions))

    def test_private_chat_never_emits_mentions(self):
        chain = build(ROSTER).reply_chain('[at:90001] 在', True, 'p')
        self.assertFalse(any(isinstance(c, At) for c in chain))

    def test_instructions_tell_her_to_write_the_marker(self):
        f = build(ROSTER)
        f.owner = 'OWNER'
        f.index = []
        f.index_path = pathlib.Path('/not-used.json')
        f.s = types.SimpleNamespace(state={}, save=lambda: None,
                                    context=types.SimpleNamespace(get_all_stars=lambda: []))
        f.cfg = {}
        f.capabilities = lambda: {'plugins': [], 'features': {}}
        text = f.public_instructions('90001')
        self.assertIn('必须写出 [at:QQ号]', text)
        self.assertIn('只写名字不会变成真正的@', text)
        self.assertIn('一次最多三个', text)
