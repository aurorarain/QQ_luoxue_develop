# All identities, messages, locations and media in this file are synthetic test fixtures.
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import test_boundaries
from luoxue_social import autonomy, books, cognition, rhythm


class Autonomy(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.target = 'napcat:FriendMessage:10001'
        self.current = dt.datetime(2026, 1, 1, 15, tzinfo=rhythm.TZ)
        self.now = self.current.timestamp()
        features = SimpleNamespace(room_state=Mock(return_value={'sleepMode': 'awake'}),
                                   mood_snapshot=Mock(return_value={'energy': 60}),
                                   pending_promises=Mock(return_value=[]),
                                   feature_flag=Mock(return_value=True), remember=Mock())
        self.social = SimpleNamespace(
            features=features, state={'owner_umo': self.target}, save=Mock(), add=Mock(),
            generate=AsyncMock(), context=SimpleNamespace(send_message=AsyncMock(return_value=False)))

    async def run_cycle(self):
        with patch.object(autonomy.time, 'time', return_value=self.now), patch.object(
                autonomy.tieba, 'node_status', return_value={'online': False}):
            await autonomy.cycle(self.social, self.current, self.target)
        return self.social.state['hb_log'][-1]

    def cool_down_routines(self):
        self.social.state['cognition'] = {'routine_cooldowns': {name: self.now + 10000 for name in cognition.ROUTINES}}

    async def test_book_progress_survives_multiple_cycles(self):
        self.cool_down_routines()
        with tempfile.TemporaryDirectory() as directory, patch.object(books, 'BOOK_DIR', Path(directory)):
            books.add_book(self.social, '示例', '示例页' * 1000)
            self.social.generate.return_value = json.dumps({'choice': 'read2'})
            self.assertEqual((await self.run_cycle())['outcome'], 'done')
            self.assertEqual(self.social.state['book_shelf']['示例']['pages_read'], 2)
            self.assertEqual(self.social.state['autonomy']['focus']['title'], '示例')
            self.now += 601
            await self.run_cycle()
            self.assertEqual(self.social.state['book_shelf']['示例']['pages_read'], 4)
            scores = self.social.state['autonomy']['last_rule_decision']['scores']
            self.assertGreater(scores[0]['preference'], 0)
            self.assertEqual(scores[0]['continuity'], 12)
            self.social.generate.assert_not_called()
            self.social.context.send_message.assert_not_called()

    def test_recover_shelf_keeps_reading_progress(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(books, 'BOOK_DIR', Path(directory)):
            books.add_book(self.social, '示例甲', '示例页' * 1000)
            books.add_book(self.social, '示例乙', '另一页' * 1000)
            books.read(self.social, '示例甲', 2)
            del self.social.state['book_shelf']['示例乙']
            books.recover_shelf(self.social)
            self.assertEqual(self.social.state['book_shelf']['示例甲']['pages_read'], 2)
            self.assertEqual(self.social.state['book_shelf']['示例乙']['pages_read'], 0)

    async def test_invalid_public_action_is_rejected(self):
        self.cool_down_routines()
        self.social.state['last_owner'] = self.now - 1800
        self.social.generate.return_value = json.dumps({'choice': 'group', 'text': '示例'})
        self.assertEqual((await self.run_cycle())['outcome'], 'failed')
        self.social.context.send_message.assert_not_called()

    async def test_unsent_message_does_not_become_a_memory_or_success(self):
        self.cool_down_routines()
        self.social.state['last_owner'] = self.now - 1800
        self.social.generate.return_value = json.dumps({'choice': 'message', 'text': '示例'})
        entry = await self.run_cycle()
        self.assertEqual(entry['outcome'], 'failed')
        self.assertNotIn('text', entry)
        self.assertNotIn('proactive', self.social.state)
        self.social.add.assert_not_called()

    async def test_asleep_does_not_invoke_the_model(self):
        self.social.features.room_state.return_value = {'sleepMode': 'asleep'}
        self.assertEqual((await self.run_cycle())['outcome'], 'idle')
        self.social.generate.assert_not_called()

    async def test_simulated_routine_requires_completion_before_reward(self):
        self.social.generate.side_effect = RuntimeError('provider unavailable')
        entry = await self.run_cycle()
        self.assertEqual(entry['outcome'], 'scheduled')
        self.assertEqual(entry['action'], 'water')
        state = self.social.state
        self.assertEqual(cognition.snapshot(state, self.now)['valence'], 0)
        cognition.advance(state, {'sleepMode': 'awake'}, self.now + 120)
        self.assertEqual(entry['outcome'], 'done')
        self.assertGreater(cognition.snapshot(state, self.now + 120)['valence'], 0)
        self.social.context.send_message.assert_not_called()
        self.social.generate.assert_not_called()

    async def test_body_threshold_and_rest_completion_are_deterministic(self):
        self.social.features.mood_snapshot.return_value = {'energy': 34, 'sleepiness': 20}
        entry = await self.run_cycle()
        self.assertEqual((entry['action'], entry['outcome']), ('rest', 'scheduled'))
        state = self.social.state
        self.assertFalse(cognition.projection(state, self.now)['episodes'])
        cognition.advance(state, {'sleepMode': 'awake'}, self.now + 900)
        self.assertEqual(entry['outcome'], 'done')
        self.assertTrue(cognition.projection(state, self.now + 900)['episodes'])
        self.social.generate.assert_not_called()

    async def test_reflection_on_lived_experience_has_no_outgoing_message(self):
        self.social.state['room_desires'] = {'触': 30}
        cognition.learn_activity(self.social.state, {'action': 'read', 'title': '样书'},
                                 {'outcome': 'done', 'result': '《样书》读到第 4 页'}, self.now - 200)
        self.social.generate.return_value = json.dumps({'feeling': '释然', 'need': '触', 'note': '慢下来就舒服多了。'})
        with patch.object(autonomy.time, 'time', return_value=self.now):
            await autonomy.reflect(self.social, '10001')
            await autonomy.reflect(self.social, '10001')
        self.assertEqual(len(self.social.state['cognition']['reflections']), 1)
        self.social.generate.assert_awaited_once()
        self.social.context.send_message.assert_not_called()

    def test_sending_respects_owner_unanswered_and_pause(self):
        state = {'owner_umo': self.target, 'last_owner': self.now - 1800}
        self.assertTrue(autonomy.message_ready(state, self.now, self.target, False))
        self.assertFalse(autonomy.message_ready(state, self.now, 'other', False))
        self.assertFalse(autonomy.message_ready(state, self.now, self.target, True))
        self.assertFalse(autonomy.message_ready(dict(state, unanswered=1), self.now, self.target, False))
        self.assertFalse(autonomy.message_ready(dict(state, proactive_enabled=False), self.now, self.target, False))
