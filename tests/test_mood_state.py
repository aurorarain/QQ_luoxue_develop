# All identities, messages, locations and media in this file are synthetic test fixtures.
import time
import types
import unittest

from test_boundaries import features


def make(state=None):
    f = features.Features.__new__(features.Features)
    f.s = types.SimpleNamespace(state=state if state is not None else {}, save=lambda: None)
    return f


class MoodDeltas(unittest.TestCase):
    def test_emotions_move_by_her_own_judgement(self):
        f = make({'room_emotions': {'喜': 40.0, '怒': 10.0}})
        applied = f.apply_mood_deltas({'emotions': {'喜': 15, '怒': -4, '不存在': 9}})
        self.assertEqual(f.s.state['room_emotions']['喜'], 55.0)
        self.assertEqual(f.s.state['room_emotions']['怒'], 6.0)
        self.assertNotIn('不存在', f.s.state['room_emotions'])
        self.assertEqual(set(applied), {'情绪喜', '情绪怒'})

    def test_one_heartbeat_cannot_jump_to_the_ceiling(self):
        f = make({'room_emotions': {'喜': 10.0}})
        f.apply_mood_deltas({'emotions': {'喜': 999}})
        self.assertEqual(f.s.state['room_emotions']['喜'], 35.0)
        f.apply_mood_deltas({'emotions': {'喜': -999}})
        self.assertEqual(f.s.state['room_emotions']['喜'], 10.0)

    def test_desires_are_capped_and_clamped(self):
        f = make({'room_desires': {'见': 20.0}, 'room_desires_at': time.time()})
        f.apply_mood_deltas({'desires': {'见': 500}})
        self.assertEqual(f.s.state['room_desires']['见'], 50.0)
        f.apply_mood_deltas({'desires': {'见': -500}})
        self.assertEqual(f.s.state['room_desires']['见'], 20.0)

    def test_garbage_never_crashes_the_heartbeat(self):
        f = make({})
        self.assertEqual(f.apply_mood_deltas(None), {})
        self.assertEqual(f.apply_mood_deltas({'emotions': 'x'}), {})
        f.apply_mood_deltas({'emotions': {'喜': 'abc', '怒': 3}})
        self.assertEqual(f.s.state['room_emotions']['喜'], 58.0)

    def test_desires_tick_down_on_their_own(self):
        f = make({'room_desires': {'见': 60.0}, 'room_desires_at': time.time() - 3600})
        f.desires()
        self.assertLess(f.s.state['room_desires']['见'], 60.0)


class LifeEvents(unittest.TestCase):
    def test_thoughts_do_not_enter_her_life(self):
        f = make({})
        self.assertFalse(f.note_life_event('鼻子堵着，想喝口热汤', 'thought', 1))
        self.assertEqual(f.s.state.get('life_events') or [], [])

    def test_important_events_enter_once(self):
        f = make({})
        self.assertTrue(f.note_life_event('今天第一次自己煮了热汤', 'life', 6))
        self.assertFalse(f.note_life_event('今天第一次自己煮了热汤', 'life', 6))
        self.assertEqual(len(f.s.state['life_events']), 1)

    def test_old_thought_rows_are_pruned_once(self):
        f = make({'life_events': [{'text': '念头', 'kind': 'thought'},
                                  {'text': '真的发生过', 'kind': 'life'}]})
        f.prune_thought_life()
        self.assertEqual([r['text'] for r in f.s.state['life_events']], ['真的发生过'])
        f.s.state['life_events'].append({'text': '又一条念头', 'kind': 'thought'})
        f.prune_thought_life()
        self.assertEqual(len(f.s.state['life_events']), 2)


class Promises(unittest.TestCase):
    def test_promise_is_recorded_then_closed(self):
        f = make({})
        self.assertTrue(f.note_promise('明天提醒主人早点睡', 6))
        self.assertFalse(f.note_promise('明天提醒主人早点睡', 6))
        self.assertEqual(len(f.pending_promises()), 1)
        self.assertTrue(f.close_promise('提醒主人'))
        self.assertEqual(f.pending_promises(), [])
        self.assertEqual(f.s.state['promises'][0]['done'], True)

    def test_closing_an_unknown_promise_changes_nothing(self):
        f = make({})
        self.assertFalse(f.close_promise('没答应过'))
        self.assertFalse(f.close_promise(''))


class Snapshot(unittest.TestCase):
    def test_snapshot_carries_every_parameter(self):
        f = make({'room_energy': 41, 'room_mood_value': 55, 'room_sleep_debt': 2})
        snap = f.mood_snapshot()
        for key in ('emotions', 'desires', 'energy', 'mood', 'sleep_debt', 'promises'):
            self.assertIn(key, snap)
        self.assertEqual(snap['energy'], 41)
        self.assertEqual(snap['mood'], 55)
        self.assertEqual(set(snap['emotions']), set(f.EMOTIONS))
        self.assertEqual(set(snap['desires']), set(f.DESIRES))

    def test_text_mood_does_not_break_the_heartbeat(self):
        # 线上真实事故：room_mood 存的是"有点无聊，想被搭理"，整次心跳 ValueError
        f = make({'room_mood': '有点无聊，想被搭理', 'room_energy': '33.4'})
        snap = f.mood_snapshot()
        self.assertEqual(snap['mood'], 60)
        self.assertEqual(snap['energy'], 33)
        self.assertEqual(snap['mood_text'], '有点无聊，想被搭理')


if __name__ == '__main__':
    unittest.main()
