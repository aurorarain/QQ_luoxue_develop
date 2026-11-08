# All identities, messages, locations and media in this file are synthetic test fixtures.
import types
import unittest
from unittest.mock import AsyncMock, patch

import test_boundaries  # noqa: F401
from test_boundaries import features
from luoxue_social.features import is_self_portrait, SELF_IMAGE
from luoxue_social.image_policy import is_draw_request


class SelfPortraitDetection(unittest.TestCase):
    def test_self_portrait_phrases(self):
        for text in ['画个自画像', '画你自己', '你长什么样', '把你自己画给我', '画洛雪']:
            self.assertTrue(is_self_portrait(text), text)

    def test_other_requests_are_not_self_portraits(self):
        for text in ['画只猫', '画小猫', '画一条肥鱼', '今天好累', '画的不错']:
            self.assertFalse(is_self_portrait(text), text)

    def test_self_image_describes_current_appearance(self):
        self.assertIn('银蓝短发', SELF_IMAGE)
        self.assertIn('异色瞳', SELF_IMAGE)


class GiveMePattern(unittest.TestCase):
    def test_draw_for_me_phrases_trigger(self):
        for text in ['把沧月画给我', '把这只猫画出来给我', '画张图给我', '把你自己画给我']:
            self.assertTrue(is_draw_request(text), text)

    def test_comments_and_unrelated_chat_still_do_not(self):
        for text in ['画的不错', '今天画画好累', '画风挺好']:
            self.assertFalse(is_draw_request(text), text)


class DrawToolPath(unittest.IsolatedAsyncioTestCase):
    def build(self):
        f = features.Features.__new__(features.Features)
        f.cfg = {'image_api': {'api_key': 'k', 'base_url': 'https://example', 'model': 'wan2.6-t2i',
                               'size': '1280*1280', 'group_daily_limit': 20}}
        f.owner = 'OWNER'
        f.s = types.SimpleNamespace(state={}, save=lambda: None)
        f.deliver_drawing = AsyncMock(return_value=True)
        f.tasks = set()
        f.draw_active = False
        return f

    def event(self, text='把沧月画给我'):
        sent = []
        event = types.SimpleNamespace(
            sent=sent, is_private_chat=lambda: True,
            get_sender_id=lambda: 'OWNER', get_message_str=lambda: text,
            unified_msg_origin='p', message_obj=types.SimpleNamespace(message_id='m', raw_message={}))
        async def send(chain):
            sent.append(chain)
        event.send = send
        return event

    async def test_tool_draws_and_prefixes_self_image(self):
        f = self.build()
        event = self.event('画个自画像')
        with patch.object(features.Features, '_generate_with_cancel', AsyncMock(return_value=b'png')):
            ok = await f.draw_from_tool(event, '画个自画像')
        self.assertTrue(ok)
        prompt = f.deliver_drawing.await_args.args[3]
        self.assertIn('银蓝短发', prompt)
        self.assertIn(SELF_IMAGE[:12], prompt)

    async def test_tool_respects_group_quota(self):
        f = self.build()
        f.s.state['image_usage'] = {'day': __import__('time').strftime('%Y-%m-%d'),
                                    'owner_count': 0, 'group_count': 20}
        event = self.event()
        event.is_private_chat = lambda: False
        event.get_sender_id = lambda: '90001'
        with patch.object(features.Features, '_generate_with_cancel', AsyncMock(return_value=b'png')):
            ok = await f.draw_from_tool(event, '画只猫')
        self.assertFalse(ok)
        f.deliver_drawing.assert_not_awaited()
