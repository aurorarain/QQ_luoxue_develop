import pathlib
import tempfile
import types
import unittest

import test_boundaries  # noqa: F401
from test_boundaries import main, features
from luoxue_social.image_policy import is_draw_request, premium_request
from luoxue_social import draw_planner


async def _collect(event, chain):
    event.sent.append(chain)


def _parts(chain):
    return getattr(chain, 'chain', chain)


class DrawIntent(unittest.TestCase):
    def test_natural_phrasings_that_used_to_be_missed(self):
        for text in ['我想要沧月图片，画一个我看看', '帮我画一只猫', '画个洛丽塔',
                     '来张壁纸', '求一张头像', '给我画个头像', '画一下今天的心情',
                     '生成一张图', '能画一张吗', '画幅画', 'draw a cat please']:
            self.assertTrue(is_draw_request(text), text)

    def test_plain_mentions_are_not_requests(self):
        for text in ['这个动画不错', '画风好评', '漫画推荐一下', '我在做计划',
                     '发张截图看看', '画质有点糊', '这张图画得不错', '我喜欢画画',
                     '', '   ']:
            self.assertFalse(is_draw_request(text), text)

    def test_premium_command_still_recognised(self):
        # The premium command is a separate path from natural-language intent.
        self.assertTrue(premium_request('/精绘26 一只鲸鱼'))
        self.assertFalse(is_draw_request('/精绘26 一只鲸鱼'))


class DrawRouting(unittest.TestCase):
    def test_owner_private_drawing_filter_uses_the_same_rule(self):
        event = types.SimpleNamespace(
            is_private_chat=lambda: True,
            get_group_id=lambda: '',
            get_sender_id=lambda: main.OWNER,
            get_message_str=lambda: '我想要沧月图片，画一个我看看')
        self.assertTrue(main.PrivateDrawing().filter(event, {}))

    def test_other_people_private_chat_never_routes_to_drawing(self):
        event = types.SimpleNamespace(
            is_private_chat=lambda: True,
            get_group_id=lambda: '',
            get_sender_id=lambda: '90001',
            get_message_str=lambda: '画一张图')
        self.assertFalse(main.PrivateDrawing().filter(event, {}))

    def test_group_draw_requests_are_handled_by_the_group_path(self):
        # In the group, drawing goes through public_chat -> draw_request, not this filter;
        # the filter only carries the owner's premium command there.
        def build(sender, text):
            return types.SimpleNamespace(
                is_private_chat=lambda: False, get_group_id=lambda: main.GROUP,
                get_sender_id=lambda: sender, get_message_str=lambda: text)
        self.assertTrue(main.PrivateDrawing().filter(build('90001', '/精绘26 鲸鱼'), {}))
        self.assertFalse(main.PrivateDrawing().filter(build('90001', '画一张图'), {}))

    def test_instructions_forbid_narrating_a_plan_as_a_drawing(self):
        f = features.Features.__new__(features.Features)
        f.s = types.SimpleNamespace(state={}, save=lambda: None,
                                    context=types.SimpleNamespace(get_all_stars=lambda: []))
        f.cfg = {}
        f.owner = 'OWNER'
        f.index = []
        f.index_path = pathlib.Path('/not-used.json')
        f.capabilities = lambda: {'plugins': [], 'features': {}}
        self.assertIn('描述画面不等于已经出图', f.public_instructions('90001'))
        self.assertIn('描述画面不等于已经出图', f.private_instructions())


class NoteBeforePicture(unittest.IsolatedAsyncioTestCase):
    def build(self):
        f = features.Features.__new__(features.Features)
        f.s = types.SimpleNamespace(state={}, save=lambda: None, add=lambda *a: None)
        f.tasks = set()
        f.root = pathlib.Path(tempfile.mkdtemp())
        return f

    async def test_assumption_note_is_sent_before_the_image(self):
        f = self.build()
        event = types.SimpleNamespace(sent=[], is_private_chat=lambda: True)
        event.send = lambda chain: _collect(event, chain)
        await f.deliver_drawing(event, b'fake-png', 'wan2.6-t2i', 'prompt text',
                                {'plan_source': 'model', 'note': '按你说的那位猜的'})
        self.assertEqual(len(event.sent), 2)
        text = ''.join(getattr(part, 'text', '') or '' for part in _parts(event.sent[0]))
        self.assertIn('猜的', text)
        self.assertEqual(_parts(event.sent[1])[0].__class__.__name__, 'Image')

    async def test_no_note_means_only_the_image(self):
        f = self.build()
        event = types.SimpleNamespace(sent=[], is_private_chat=lambda: True)
        event.send = lambda chain: _collect(event, chain)
        await f.deliver_drawing(event, b'fake-png', 'wan2.6-t2i', 'prompt text', {'plan_source': 'model'})
        self.assertEqual(len(event.sent), 1)

    async def test_truncated_json_still_yields_a_prompt(self):
        async def generate(prompt, system, **kwargs):
            return '{"subject":"猫","prompt":"一只橘猫趴在窗台上，午后暖光，插画风格，线条干净'
        social = types.SimpleNamespace(state={'group': []}, generate=generate, save=lambda: None,
                                       group_memory=lambda text: [])
        result = await draw_planner.plan(social, None, '画一只猫', False)
        self.assertEqual(result['plan_source'], 'model')
        self.assertIn('橘猫', result['prompt'])

    async def test_planner_exposes_and_sanitizes_the_note(self):
        async def generate(prompt, system, **kwargs):
            return '{"prompt":"一只猫坐在窗台上，暖色插画","note":"按你说的那只猜的 https://evil.example 12345678901"}'
        social = types.SimpleNamespace(state={'group': []}, generate=generate, save=lambda: None,
                                       group_memory=lambda text: [])
        result = await draw_planner.plan(social, None, '画一只猫', False)
        self.assertIn('猜的', result['note'])
        self.assertNotIn('http', result['note'])
        self.assertNotIn('12345678901', result['note'])
