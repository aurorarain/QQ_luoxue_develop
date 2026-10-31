import asyncio
import types
import unittest
from unittest.mock import AsyncMock, patch

import test_boundaries  # noqa: F401
from test_boundaries import main, features
from astrbot.api.message_components import Image


class FakeEvent:
    def __init__(self, text='', sender='90001', private=False, group=None,
                 components=None, message_id='m1'):
        self.message_str = text
        self.stopped = False
        self.private = private
        self.sender = sender
        self.group = group or main.GROUP
        self.message_obj = types.SimpleNamespace(
            raw_message={'post_type': 'message', 'message': []},
            message=list(components or []), message_id=message_id)
        self.sent = []

    def is_private_chat(self): return self.private
    def get_sender_id(self): return self.sender
    def get_group_id(self): return self.group
    def get_self_id(self): return 'BOT'
    def get_message_str(self): return self.message_str
    def get_messages(self): return self.message_obj.message
    def stop_event(self): self.stopped = True

    @property
    def unified_msg_origin(self):
        return ('napcat:FriendMessage:' if self.private else 'napcat:GroupMessage:') + self.sender


class FakeFeatures:
    def __init__(self):
        self.combos = []
        self.quotes = []

    def note_sticker_combo(self, event, text):
        self.combos.append(text)

    def should_quote(self, event):
        return bool(self.quotes)

    def reply_chain(self, text, private, session):
        return [types.SimpleNamespace(text=text, __class__=type('Plain', (), {}))]


class MediaTurnMerge(unittest.IsolatedAsyncioTestCase):
    def build(self):
        social = main.Social.__new__(main.Social)
        social.state = {}
        social.save = lambda: None
        social.text_media_wait = 0.06
        social._pending_media = {}
        social.features = FakeFeatures()
        return social

    async def test_text_then_picture_becomes_one_turn(self):
        social = self.build()
        text_event = FakeEvent('这个可爱吗')
        picture = Image(file='https://example.org/sticker.gif')
        image_event = FakeEvent('', components=[picture])
        task = asyncio.create_task(social.turn_gate(text_event))
        await asyncio.sleep(0.01)
        await social.turn_gate(image_event)
        await asyncio.wait_for(task, timeout=2)
        self.assertTrue(image_event.stopped)
        self.assertIn('这个可爱吗', text_event.message_str)
        self.assertIn('同时发来一张图片', text_event.message_str)
        self.assertIn(picture, text_event.message_obj.message)
        self.assertEqual(social.features.combos, ['这个可爱吗'])

    async def test_two_text_messages_stay_separate(self):
        social = self.build()
        first, second = FakeEvent('第一句'), FakeEvent('第二句')
        await asyncio.wait_for(social.turn_gate(first), timeout=2)
        await asyncio.wait_for(social.turn_gate(second), timeout=2)
        self.assertEqual(first.message_str, '第一句')
        self.assertEqual(second.message_str, '第二句')
        self.assertFalse(first.stopped or second.stopped)

    async def test_text_and_picture_in_one_message_counts_as_combo(self):
        social = self.build()
        event = FakeEvent('看这个表情', components=[Image(file='https://example.org/a.gif')])
        await social.turn_gate(event)
        self.assertEqual(social.features.combos, ['看这个表情'])

    async def test_commands_and_stop_are_never_held(self):
        social = self.build()
        for text in ('/说话 你好', '停'):
            event = FakeEvent(text)
            await asyncio.wait_for(social.turn_gate(event), timeout=1)
            self.assertEqual(event.message_str, text)


class StickerCombo(unittest.IsolatedAsyncioTestCase):
    def build(self):
        f = features.Features.__new__(features.Features)
        f.s = types.SimpleNamespace(state={}, save=lambda: None)
        f.tasks = set()
        f.collect = AsyncMock()
        return f

    def event(self, url='https://example.org/sticker.gif'):
        return types.SimpleNamespace(
            is_private_chat=lambda: False,
            message_obj=types.SimpleNamespace(raw_message={
                'message': [{'type': 'image', 'data': {'url': url}}]}))

    async def test_third_identical_pair_triggers_collection(self):
        f = self.build()
        for _ in range(2):
            f.note_sticker_combo(self.event(), '看这个猫')
        self.assertEqual(f.collect.await_count, 0)
        f.note_sticker_combo(self.event(), '看这个猫')
        await asyncio.gather(*list(f.tasks), return_exceptions=True)
        self.assertEqual(f.collect.await_count, 1)
        entry = next(iter(f.s.state['sticker_combos'].values()))
        self.assertTrue(entry['collected'])
        self.assertEqual(entry['count'], 3)

    async def test_different_text_does_not_count_together(self):
        f = self.build()
        f.note_sticker_combo(self.event(), '第一句')
        f.note_sticker_combo(self.event(), '第二句')
        f.note_sticker_combo(self.event(), '第三句')
        await asyncio.gather(*list(f.tasks), return_exceptions=True)
        self.assertEqual(f.collect.await_count, 0)

    async def test_private_and_group_scope_is_passed_through(self):
        f = self.build()
        private_event = types.SimpleNamespace(
            is_private_chat=lambda: True,
            message_obj=types.SimpleNamespace(raw_message={
                'message': [{'type': 'image', 'data': {'url': 'https://example.org/p.gif'}}]}))
        for _ in range(3):
            f.note_sticker_combo(private_event, '这个给你')
        await asyncio.gather(*list(f.tasks), return_exceptions=True)
        self.assertTrue(f.collect.await_args.args[1])


class Quote(unittest.IsolatedAsyncioTestCase):
    def test_quote_only_when_multiple_people_talk(self):
        f = features.Features.__new__(features.Features)
        f.s = types.SimpleNamespace(state={'group_observed': [
            {'sender': '90001', 'text': 'a'}, {'sender': '90002', 'text': 'b'}]}, save=lambda: None)
        self.assertTrue(f.should_quote(FakeEvent('x')))
        f.s.state['group_observed'] = [{'sender': '90001', 'text': 'a'}, {'sender': '90001', 'text': 'b'}]
        self.assertFalse(f.should_quote(FakeEvent('x')))

    def test_private_quote_only_after_several_messages(self):
        import time
        f = features.Features.__new__(features.Features)
        now = time.time()
        f.s = types.SimpleNamespace(state={'private': [{'time': now - 5, 'sender': main.OWNER, 'text': 'a'}]},
                                    save=lambda: None)
        self.assertFalse(f.should_quote(FakeEvent('x', private=True)))
        f.s.state['private'].append({'time': now - 3, 'sender': main.OWNER, 'text': 'b'})
        self.assertTrue(f.should_quote(FakeEvent('x', private=True)))
