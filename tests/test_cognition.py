import unittest

import test_boundaries
from luoxue_social import cognition
from test_brain_api import room_api
from test_mood_state import make


class CognitiveLoop(unittest.TestCase):
    def test_same_words_feel_different_based_on_body_and_need(self):
        rested = {'room_energy': 75, 'room_desires': {'触': 25}}
        tired = {'room_energy': 28, 'room_desires': {'触': 85}}
        for state in (rested, tired):
            cognition.observe_owner(state, '谢谢你', 10000)
        stronger = cognition.affect_overlay(rested, 10000, owner=True)
        weaker = cognition.affect_overlay(tired, 10000, owner=True)
        self.assertGreater(stronger['emotions']['喜'], weaker['emotions']['喜'])
        self.assertGreater(stronger['emotions']['爱'], weaker['emotions']['爱'])
        self.assertGreater(stronger['needs']['触'], weaker['needs']['触'])
        self.assertEqual(cognition.affect_overlay(rested, 10000)['emotions'], {})

    def test_unmet_need_can_reactivate_a_past_private_event_once(self):
        now = 10000
        state = {'room_desires': {'意': 30},
                 'private': [{'time': now - 120, 'sender': '90001', 'text': '我把还没做完的实验放到周末了'}]}
        candidate = cognition.reflection_candidate(state, '90001', now)
        self.assertEqual(candidate['need'], '意')
        cognition.reserve_reflection(state, candidate, now)
        self.assertTrue(cognition.finish_reflection(state, candidate, {'feeling': '好奇', 'need': '意'}, now))
        self.assertGreater(cognition.affect_overlay(state, now, owner=True)['emotions']['欲'], 0)
        self.assertLess(cognition.needs_level(state, '意', now, owner=True), 30)
        self.assertEqual(cognition.snapshot(state, now)['valence'], 0)
        self.assertIsNone(cognition.reflection_candidate(state, '90001', now + 1799))
        self.assertIsNone(cognition.reflection_candidate(state, '90001', now + 1801))
        state['memory_off'] = True
        self.assertEqual(cognition.projection(state, now)['reflections'], [])

    def test_verified_feedback_has_a_private_signal_and_retrievable_cue(self):
        now, state = 10000, {}
        cognition.observe_owner(state, '阅读分享得好，谢谢你', now)
        self.assertGreater(cognition.snapshot(state, now, owner=True)['prediction'], 0)
        self.assertEqual(cognition.snapshot(state, now)['valence'], 0)
        self.assertEqual(cognition.relevant(state, '继续阅读吗', now), [])
        self.assertNotIn('受到肯定', cognition.private_context(state, '继续阅读吗', now))
        self.assertIn('受到肯定', cognition.private_context(state, '继续阅读吗', now + 5))
        self.assertNotIn('阅读分享得好', str(state))
        self.assertEqual(cognition.relevant(state, '今天天气怎样', now, owner=True), [])
        self.assertLess(cognition.snapshot(state, now + 5400, owner=True)['valence'],
                        cognition.snapshot(state, now, owner=True)['valence'])
        cognition.observe_owner(state, '你这次说错了', now + 5400)
        self.assertGreater(cognition.snapshot(state, now + 5400, owner=True)['stress'], 0)
        state['memory_off'] = True
        self.assertEqual(cognition.private_context(state, '继续阅读吗', now), '')
        self.assertFalse(cognition.projection(state, now)['episodes'])

    def test_repeated_outcome_habituates_and_ranks_against_failed_choice(self):
        now, state = 10000, {}
        good = {'action': 'read', 'title': '例书甲'}
        bad = {'action': 'read', 'title': '例书乙'}
        cognition.learn_activity(state, good, {'outcome': 'done', 'result': '《例书甲》读到第 2 页'}, now)
        cognition.learn_activity(state, good, {'outcome': 'done', 'result': '《例书甲》读到第 4 页'}, now + 300)
        cognition.learn_activity(state, bad, {'outcome': 'failed'}, now + 300)
        rows = state['cognition']['episodes']
        self.assertLess(rows[1]['surprise'], rows[0]['surprise'])
        self.assertGreater(cognition.learned_value(state, good, now + 300), 0)
        self.assertLess(cognition.learned_value(state, bad, now + 300), 0)

    def test_sleep_only_consolidates_a_real_eligible_episode_once(self):
        now, state = 10000, {}
        cognition.learn_activity(state, {'action': 'read'}, {'outcome': 'done', 'result': '读完一节'}, now)
        cognition.advance(state, {'sleepMode': 'asleep'}, now + 60)
        cognition.advance(state, {'sleepMode': 'asleep'}, now + 1810)
        self.assertFalse(state['cognition'].get('consolidated_count'))
        cognition.advance(state, {'sleepMode': 'asleep'}, now + 1860)
        cognition.advance(state, {'sleepMode': 'asleep'}, now + 2000)
        self.assertEqual(state['cognition']['consolidated_count'], 1)
        self.assertTrue(state['cognition']['episodes'][0]['consolidated'])

    def test_public_emotion_projection_and_protected_graph(self):
        now, state = 10000, {}
        f = make(state)
        initial = f.projected_emotions(now)['喜']
        cognition.learn_activity(state, {'action': 'read'}, {'outcome': 'done', 'result': '读完一节'}, now)
        self.assertGreater(f.projected_emotions(now)['喜'], initial)
        state['cognition_view'] = cognition.projection(state, now)
        graph = room_api.brain_payload(state, now)
        self.assertEqual(graph['cognition']['episodes'][0]['label'], '读完一节')
        self.assertTrue(any(link['kind'] == 'episode-action' for link in graph['links']))

    def test_refresh_does_not_round_away_emotion_decay(self):
        f = make({'room_emotions': {'喜': 28}, 'room_emotions_at': 10000})
        for index in range(1, 181):
            f.emotions(10000 + index * 20)
        self.assertAlmostEqual(f.emotions(13600)['喜'], 22 + 6 * .5 ** (1 / 2.5), places=5)

    def test_direct_title_and_explicit_recall_do_not_need_model_guessing(self):
        state = {}
        cognition.learn_activity(state, {'action': 'read', 'title': '样书甲'},
                                 {'outcome': 'done', 'result': '《样书甲》读到第 8 页'}, 10000)
        cognition.learn_activity(state, {'action': 'read', 'title': '样书乙'},
                                 {'outcome': 'done', 'result': '《样书乙》读到第 2 页'}, 10010)
        recalled = cognition.private_context(state, '你上次读样书甲到哪了？', 10015)
        self.assertIn('第 8 页', recalled)
        self.assertIn('用上面的已记录经历直接接话', recalled)
        self.assertIn('样书乙', cognition.private_context(state, '你上次做了什么？', 10015))
        self.assertNotIn('样书', cognition.private_context(state, '天气怎样？', 10015))
