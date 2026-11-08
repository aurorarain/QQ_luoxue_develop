# All identities, messages, locations and media in this file are synthetic test fixtures.
import unittest
import test_boundaries  # noqa: F401  (installs the astrbot stubs and sys.path)
from luoxue_social import persona


def full_text():
    """底层人设 + 全部成长特质，合起来才是她完整的性格文本。"""
    return persona.CORE_PROMPT + '\n' + persona.GROWTH_EXTRA_TEXT


class PersonaLayers(unittest.TestCase):
    def test_three_layers_exist_and_stay_her_own(self):
        for phrase in ('你的性格有三层', '高贵又聪明、嘴硬心软', '给自己加设定', '不是扮演别人'):
            self.assertIn(phrase, full_text())

    def test_no_roleplay_ip_is_baked_into_the_character(self):
        # Traits may be inspired by characters, but the persona must never name them or
        # carry their lines: that would turn her into someone else's script.
        for name in ('辉夜', '六花', '邪王', '会长'):
            self.assertNotIn(name, full_text())
        self.assertIn('不引用任何作品的梗', full_text())

    def test_frequency_guard_and_serious_context_switch(self):
        self.assertIn('每五六轮', full_text())
        self.assertIn('有人难过时，这两层全部收起来', full_text())
