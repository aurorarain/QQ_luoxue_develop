import pathlib
import types
import unittest

import test_boundaries  # noqa: F401
from test_boundaries import features


def build(index=None):
    f = features.Features.__new__(features.Features)
    f.s = types.SimpleNamespace(state={}, save=lambda: None,
                                context=types.SimpleNamespace(get_all_stars=lambda: []))
    f.cfg = {}
    f.owner = 'OWNER'
    f.index = index or []
    f.index_path = pathlib.Path('/not-used.json')
    f.capabilities = lambda: {'plugins': [], 'features': {}, 'plugin_root': '/not-used'}
    return f


class CapabilityUsage(unittest.TestCase):
    def test_private_instructions_hand_over_the_real_tools(self):
        text = build().private_instructions()
        for phrase in ('change_my_signature 一天最多改一次', 'change_my_status 跟着作息走',
                       'parse_media_url', 'qq_tools 的只读查询'):
            self.assertIn(phrase, text)

    def test_signature_rules_forbid_private_details(self):
        text = build().private_instructions()
        self.assertIn('绝不写私聊细节', text)

    def test_link_parsing_must_not_pretend_to_have_watched(self):
        text = build().private_instructions()
        self.assertIn('不能假装看完视频或全文', text)

    def test_nickname_and_avatar_stay_with_the_owner(self):
        text = build().private_instructions()
        self.assertIn('昵称和头像不归你改', text)
        self.assertNotIn('change_my_nickname ', text)
