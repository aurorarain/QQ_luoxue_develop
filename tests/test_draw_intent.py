import pathlib
import tempfile
import types
import unittest

from unittest.mock import AsyncMock, patch

import test_boundaries  # noqa: F401
from test_boundaries import main, features
from luoxue_social.image_policy import is_draw_request, premium_request
from luoxue_social import draw_planner


async def _collect(event, chain):
    event.sent.append(chain)


def _parts(chain):
    return getattr(chain, 'chain', chain)


class DrawIntent(unittest.TestCase):
    def test_short_imperatives_work_and_hobbies_do_not(self):
        self.assertTrue(is_draw_request('画沧月'))
        self.assertTrue(is_draw_request('画只猫'))
        for text in ['画画', '画风不错', '画质糊了', '画师叫什么', '画笔在哪']:
            self.assertFalse(is_draw_request(text), text)

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


class DrawAckAndFailure(unittest.IsolatedAsyncioTestCase):
    def build(self, failing=False):
        f = features.Features.__new__(features.Features)
        f.s = types.SimpleNamespace(
            state={}, save=lambda: None, add=lambda *a: None,
            generate=AsyncMock(return_value='{"prompt":"一位少女站在月光下的冰湖上，冷色调插画"}'))
        f.cfg = {'image_api': {'provider': 'dashscope', 'api_key': 'k', 'base_url': 'https://example',
                               'model': 'wan2.6-t2i', 'size': '1280*1280', 'group_daily_limit': 20}}
        f.owner = 'OWNER'
        f.index = []
        f.root = pathlib.Path(tempfile.mkdtemp())
        f.tasks = set()
        f.roster_cache = []
        self.failing = failing
        return f

    def event(self):
        event = types.SimpleNamespace(sent=[], is_private_chat=lambda: False,
                                      get_sender_id=lambda: '90001',
                                      get_group_id=lambda: main.GROUP,
                                      unified_msg_origin='napcat:GroupMessage:' + main.GROUP,
                                      get_message_str=lambda: '画沧月',
                                      get_messages=lambda: [])
        event.send = lambda chain: _collect(event, chain)
        return event

    async def test_acknowledges_before_generating(self):
        f = self.build()
        event = self.event()
        from unittest.mock import AsyncMock as AM
        with patch('luoxue_social.image_api.generate', AM(return_value=b'fake-png')):
            await f.draw_request(event, '画沧月')
        first = ''.join(getattr(part, 'text', '') or '' for part in _parts(event.sent[0]))
        self.assertTrue(any(word in first for word in ('收到', '这就画', '在画了')))
        self.assertEqual(_parts(event.sent[-1])[0].__class__.__name__, 'Image')

    async def test_failure_is_reported_instead_of_silence(self):
        f = self.build()
        event = self.event()
        from unittest.mock import AsyncMock as AM
        with patch('luoxue_social.image_api.generate', AM(side_effect=TimeoutError('boom'))):
            handled = await f.draw_request(event, '画沧月')
        self.assertTrue(handled)
        texts = [''.join(getattr(part, 'text', '') or '' for part in _parts(chain)) for chain in event.sent]
        self.assertTrue(any('没画出来' in text for text in texts), texts)
        self.assertEqual(f.s.state.get('drawing_history') or [], [])


class PrivatePoke(unittest.IsolatedAsyncioTestCase):
    def test_filter_accepts_only_the_owner_poking_the_bot_privately(self):
        def event(private, sender, raw):
            return types.SimpleNamespace(is_private_chat=lambda: private,
                                         get_sender_id=lambda: sender,
                                         get_self_id=lambda: 'BOT',
                                         message_obj=types.SimpleNamespace(raw_message=raw))
        self.assertTrue(main.OwnerPoke().filter(event(True, main.OWNER, {'notice_type': 'poke', 'target_id': 'BOT'}), {}))
        self.assertTrue(main.OwnerPoke().filter(event(True, main.OWNER, {'sub_type': 'poke'}), {}))
        self.assertFalse(main.OwnerPoke().filter(event(True, '90001', {'notice_type': 'poke'}), {}))
        self.assertFalse(main.OwnerPoke().filter(event(False, main.OWNER, {'notice_type': 'poke'}), {}))
        self.assertFalse(main.OwnerPoke().filter(event(True, main.OWNER, {'notice_type': 'group_increase'}), {}))

    async def test_poke_reply_is_sent(self):
        social = main.Social.__new__(main.Social)
        social.state = {}
        social.save = lambda: None
        event = types.SimpleNamespace(sent=[], is_private_chat=lambda: True,
                                      get_sender_id=lambda: main.OWNER,
                                      message_obj=types.SimpleNamespace(raw_message={'notice_type': 'poke'}))
        event.send = lambda chain: _collect(event, chain)
        event.stop_event = lambda: None
        await main.Social.private_poke(social, event)
        self.assertEqual(len(event.sent), 1)
        text = ''.join(getattr(part, 'text', '') or '' for part in _parts(event.sent[0]))
        self.assertTrue(text)


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
