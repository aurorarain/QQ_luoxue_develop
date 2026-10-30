import unittest
import test_boundaries  # noqa: F401  (installs the astrbot stubs and sys.path)
from luoxue_social import persona


class PersonaLayers(unittest.TestCase):
    def test_three_layers_exist_and_stay_her_own(self):
        for phrase in ('你的性格有三层', '高贵又聪明、嘴硬心软', '给自己加设定', '不是扮演别人'):
            self.assertIn(phrase, persona.PERSONA)

    def test_no_roleplay_ip_is_baked_into_the_character(self):
        # Traits may be inspired by characters, but the persona must never name them or
        # carry their lines: that would turn her into someone else's script.
        for name in ('辉夜', '六花', '邪王', '会长'):
            self.assertNotIn(name, persona.PERSONA)
        self.assertIn('不引用任何作品的梗', persona.PERSONA)

    def test_frequency_guard_and_serious_context_switch(self):
        self.assertIn('每五六轮', persona.PERSONA)
        self.assertIn('有人难过时，这两层全部收起来', persona.PERSONA)
