import asyncio
import pathlib
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, patch

import test_boundaries  # noqa: F401
from test_boundaries import main, features
from luoxue_social.image_policy import is_draw_request, is_stop_command


def _parts(chain):
    return getattr(chain, 'chain', chain)


def _collect(event, chain):
    event.sent.append(chain)


async def _send(event, chain):
    event.sent.append(chain)


class PraiseIsNotARequest(unittest.TestCase):
    def test_praise_and_comments_do_not_start_a_drawing(self):
        for text in ['画的不错', '画得不错', '画的挺好', '画得好棒', '画完了吗', '画过几张',
                     '画工不错', '画技可以', '画画', '画风好看', '画质糊了']:
            self.assertFalse(is_draw_request(text), text)

    def test_real_short_requests_still_work(self):
        for text in ['画沧月', '画只猫', '画个洛丽塔', '画一张图', '帮我画一只猫']:
            self.assertTrue(is_draw_request(text), text)

    def test_stop_commands(self):
        for text in ['停', '停下', '别画了', '不用画了', '取消画']:
            self.assertTrue(is_stop_command(text), text)
        for text in ['停一下车', '别画蛇添足', '好看']:
            self.assertFalse(is_stop_command(text), text)


class StopCancelsGeneration(unittest.IsolatedAsyncioTestCase):
    def build(self):
        f = features.Features.__new__(features.Features)
        f.s = types.SimpleNamespace(
            state={}, save=lambda: None,
            add=lambda *a: None,
            generate=AsyncMock(return_value='{"prompt":"一位少女站在月光下的冰湖上，冷色调插画"}'))
        f.cfg = {'image_api': {'provider': 'dashscope', 'api_key': 'k', 'base_url': 'https://example',
                               'model': 'wan2.6-t2i', 'size': '1280*1280', 'group_daily_limit': 20}}
        f.owner = 'OWNER'
        f.index = []
        f.root = pathlib.Path(tempfile.mkdtemp())
        f.tasks = set()
        f.roster_cache = []
        f.draw_cancel = asyncio.Event()
        f.draw_requester = ''
        f.draw_active = False
        return f

    def event(self, text='画沧月'):
        event = types.SimpleNamespace(sent=[], is_private_chat=lambda: False,
                                      get_sender_id=lambda: '90001',
                                      get_group_id=lambda: main.GROUP,
                                      unified_msg_origin='napcat:GroupMessage:' + main.GROUP,
                                      get_message_str=lambda: text,
                                      get_messages=lambda: [])
        event.send = lambda chain: _send(event, chain)
        return event

    async def test_stop_aborts_the_picture_and_says_so(self):
        f = self.build()
        event = self.event()

        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(5)
            return b'fake-png'

        with patch('luoxue_social.image_api.generate', slow_generate):
            task = asyncio.create_task(f.draw_request(event, '画沧月'))
            await asyncio.sleep(0.2)
            self.assertTrue(f.draw_active)
            f.cancel_drawing()
            handled = await asyncio.wait_for(task, timeout=5)
        self.assertTrue(handled)
        texts = [''.join(getattr(part, 'text', '') or '' for part in _parts(chain)) for chain in event.sent]
        self.assertTrue(any('停了' in text for text in texts), texts)
        self.assertFalse(any('Image' in chain.__class__.__name__ for chain in event.sent))
        self.assertEqual(f.s.state.get('drawing_history') or [], [])
        self.assertFalse(f.draw_active)

    async def test_without_stop_the_picture_is_delivered(self):
        f = self.build()
        event = self.event()
        with patch('luoxue_social.image_api.generate', AsyncMock(return_value=b'fake-png')):
            await f.draw_request(event, '画沧月')
        self.assertTrue(f.s.state.get('drawing_history'))
        self.assertTrue(f.s.state['drawing_history'][-1]['delivered'])


class PrivateStop(unittest.IsolatedAsyncioTestCase):
    async def test_private_stop_sets_the_flag(self):
        social = main.Social.__new__(main.Social)
        social.features = types.SimpleNamespace(draw_active=True, cancel_drawing=lambda: setattr(social, 'cancelled', True))
        event = types.SimpleNamespace(sent=[], is_private_chat=lambda: True,
                                      get_sender_id=lambda: main.OWNER,
                                      get_message_str=lambda: '停')
        event.send = lambda chain: _send(event, chain)
        event.stop_event = lambda: None
        await main.Social.stop_drawing(social, event)
        self.assertTrue(getattr(social, 'cancelled', False))
        self.assertEqual(len(event.sent), 1)
