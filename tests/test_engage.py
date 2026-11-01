# All identities, messages, locations and media in this file are synthetic test fixtures.
import datetime as dt
import pathlib
import random
import tempfile
import time
import types
import unittest
from unittest.mock import AsyncMock

import test_boundaries  # noqa: F401
from test_boundaries import features
from luoxue_social import engage
from luoxue_social.rhythm import TZ


class ChimeScore(unittest.TestCase):
    def test_mentions_of_her_or_the_owner_score_much_higher(self):
        plain, _ = engage.chime_score('今天地铁好挤啊')
        about_her, reason = engage.chime_score('洛雪今天怎么没说话')
        about_owner, _ = engage.chime_score('老大今天又加班')
        self.assertLess(plain, 0.1)
        self.assertGreater(about_her, 0.5)
        self.assertGreater(about_owner, 0.35)
        self.assertIn('self', reason)

    def test_short_links_and_serious_topics_never_chime(self):
        for text in ['1', 'https://example.org/x', '今天真的很难受，压力好大', '']:
            score, _ = engage.chime_score(text)
            self.assertEqual(score, 0.0, text)

    def test_should_try_respects_probability(self):
        class Always:
            def random(self):
                return 0.0
        class Never:
            def random(self):
                return 0.99
        self.assertTrue(engage.should_try(0.2, Always()))
        self.assertFalse(engage.should_try(0.2, Never()))
        self.assertFalse(engage.should_try(0.0, Always()))


class ReminderParse(unittest.TestCase):
    def now(self):
        return dt.datetime(2026, 11, 1, 9, 0, tzinfo=TZ)

    def test_relative_minutes_and_hours(self):
        due = engage.parse_reminder('20分钟后提醒我喝水', now=self.now())
        self.assertAlmostEqual(due - self.now().timestamp(), 20 * 60, delta=2)
        due = engage.parse_reminder('2小时后开会', now=self.now())
        self.assertAlmostEqual(due - self.now().timestamp(), 2 * 3600, delta=2)

    def test_clock_forms(self):
        due = engage.parse_reminder('今天18:30 跑步', now=self.now())
        target = dt.datetime(2026, 11, 1, 18, 30, tzinfo=TZ)
        self.assertAlmostEqual(due, target.timestamp(), delta=2)
        due = engage.parse_reminder('明天9点 交作业', now=self.now())
        target = dt.datetime(2026, 11, 2, 9, 0, tzinfo=TZ)
        self.assertAlmostEqual(due, target.timestamp(), delta=2)

    def test_past_today_time_rolls_to_tomorrow(self):
        due = engage.parse_reminder('今天8:00 已经过了', now=self.now())
        target = dt.datetime(2026, 11, 2, 8, 0, tzinfo=TZ)
        self.assertAlmostEqual(due, target.timestamp(), delta=2)

    def test_unparseable(self):
        self.assertIsNone(engage.parse_reminder('随便写点什么', now=self.now()))


def build(state=None, cfg=None):
    f = features.Features.__new__(features.Features)
    f.s = types.SimpleNamespace(state=state if state is not None else {}, save=lambda: None)
    f.cfg = cfg or {}
    f.index = [{'file': '开心/肥鱼_0001_笑.gif', 'category': '开心', 'scope': 'public'},
               {'file': '傲娇/肥鱼_0002_哼.gif', 'category': '傲娇', 'scope': 'public'}]
    f.library = pathlib.Path('/not-used')
    f.index_path = pathlib.Path('/not-used.json')
    f.root = pathlib.Path(tempfile.mkdtemp())
    f.tasks = set()
    return f


class ReminderStore(unittest.TestCase):
    def test_add_list_delete_and_due(self):
        f = build()
        row = f.add_reminder('喝水', time.time() + 60)
        self.assertEqual(len(f.list_reminders()), 1)
        self.assertEqual(f.due_reminders(), [])
        self.assertTrue(f.delete_reminder(row['id']))
        self.assertEqual(f.list_reminders(), [])

    def test_due_marks_sent_once(self):
        f = build()
        f.add_reminder('交作业', time.time() - 5)
        first = f.due_reminders()
        second = f.due_reminders()
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])


class StickerAndSong(unittest.TestCase):
    def test_sticker_index_groups_meanings(self):
        index = build().sticker_index()
        self.assertEqual(index['开心'], ['肥鱼_0001_笑'])
        self.assertEqual(index['傲娇'], ['肥鱼_0002_哼'])

    def test_song_picker_prefers_match_then_any(self):
        f = build()
        folder = f.root / 'songs'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / '稻香.mp3').write_bytes(b'x')
        (folder / '晴天.wav').write_bytes(b'x')
        self.assertEqual(features.Features.play_song(f, '晴天').name, '晴天.wav')
        self.assertIn(features.Features.play_song(f, '').name, {'稻香.mp3', '晴天.wav'})

    def test_empty_song_folder_returns_none(self):
        f = build()
        self.assertIsNone(f.play_song(''))


class MaybeChime(unittest.IsolatedAsyncioTestCase):
    def build(self):
        f = build()
        f.cfg = {}
        f.s.generate = AsyncMock(return_value='这句我能不能插一句')
        f.s.context = types.SimpleNamespace(get_all_stars=lambda: [])
        return f

    async def test_skips_when_model_says_skip(self):
        f = self.build()
        f.s.generate = AsyncMock(return_value='SKIP')
        self.assertIsNone(await f.maybe_chime(object(), '洛雪今天怎么不说话'))

    async def test_cooldown_blocks_second_chime(self):
        f = self.build()
        f.s.state['chime_last'] = time.time()
        self.assertIsNone(await f.maybe_chime(object(), '洛雪在吗'))

    async def test_daily_cap(self):
        f = self.build()
        f.s.state['chime_usage'] = {'day': time.strftime('%Y-%m-%d'), 'count': 6}
        self.assertIsNone(await f.maybe_chime(object(), '洛雪在吗'))

    async def test_unrelated_topic_usually_silent(self):
        f = self.build()
        random.seed(0)
        results = [await f.maybe_chime(object(), '今天地铁好挤啊') for _ in range(5)]
        self.assertTrue(all(item is None for item in results))
