import datetime as dt
import unittest
from unittest.mock import AsyncMock, patch

from test_boundaries import main, features, Event
from luoxue_social import rhythm
from luoxue_social.companion import Companion
from luoxue_social.features import split_reply


def at(hour, minute=0):
    return dt.datetime(2026, 10, 30, hour, minute, tzinfo=rhythm.TZ)


class SplitReply(unittest.TestCase):
    def test_short_and_structured_replies_stay_whole(self):
        self.assertEqual(split_reply('好'), ['好'])
        self.assertEqual(len(split_reply('这是很短的一句回话。')), 1)
        code = '看这段：\n```bash\ndocker ps\n```\n就这样。'
        self.assertEqual(split_reply(code), [code])
        bullets = '- 第一件事，要注意这个\n- 第二件事，也要注意\n- 第三件事，别忘了'
        self.assertEqual(split_reply(bullets), [bullets])

    def test_long_reply_splits_into_at_most_three_bubbles(self):
        text = '今天真的有点累。不过看到你回来我还是挺开心的。白米饭我留了半碗。要不要先歇一会？'
        chunks = split_reply(text)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertLessEqual(len(chunks), 3)
        self.assertEqual(''.join(chunks), text)
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_no_empty_chunks_for_punctuation_only(self):
        self.assertEqual(split_reply('。'), ['。'])
        self.assertEqual(split_reply('   '), [])


class Rhythm(unittest.TestCase):
    def test_phases_cover_the_day(self):
        expected = {2: '深夜', 7: '清晨', 10: '上午', 12: '午饭', 14: '午后', 16: '下午', 19: '傍晚', 23: '夜里'}
        for hour, phase in expected.items():
            self.assertEqual(rhythm.phase(at(hour))['phase'], phase, hour)

    def test_context_is_role_state_not_physiology(self):
        text = rhythm.context(at(2))
        self.assertIn('深夜', text)
        self.assertIn('北京时间2点', text)
        self.assertIn('不是真实生理', text)


class Atmosphere(unittest.TestCase):
    def build(self):
        social = type('S', (), {'state': {}, 'save': lambda self: None})()
        return Companion(social), social

    def test_warm_and_tease_carry_over_then_decay(self):
        companion, social = self.build()
        self.assertIn('小得意', companion.atmosphere('谢谢，好可爱', now=1000))
        self.assertIn('气氛还没散', companion.atmosphere('笨蛋，不服来战', now=1000))
        self.assertEqual(companion.atmosphere('嗯', now=1000 + 2000), '')

    def test_low_mood_suppresses_jokes(self):
        companion, _ = self.build()
        self.assertIn('收住玩笑', companion.atmosphere('今天太累了', now=500))


class VoiceAndStatus(unittest.IsolatedAsyncioTestCase):
    async def test_send_reply_chunks_and_keeps_last_bubble_assets(self):
        f = features.Features.__new__(features.Features)
        f.s = type('S', (), {'state': {}, 'save': lambda self: None})()
        f.roster_cache = []
        f.choose_meme = lambda *a, **k: None
        event = Event(sender='90001', text='随便聊聊')
        with patch('luoxue_social.features.asyncio.sleep', AsyncMock()):
            await f.send_reply(event, '今天真的有点累。不过看到你回来我还是挺开心的。白米饭我留了半碗。')
        self.assertGreaterEqual(len(event.sent), 2)

    async def test_proactive_voice_is_bounded(self):
        f = features.Features.__new__(features.Features)
        f.s = type('S', (), {'state': {}, 'save': lambda self: None})()
        self.assertFalse(f.proactive_voice_allowed('这一条回复很长' * 20))
        f.s.state['proactive_voice'] = {'day': __import__('time').strftime('%Y-%m-%d'), 'count': 3}
        self.assertFalse(f.proactive_voice_allowed('晚安'))

    async def test_self_status_reports_runtime_facts(self):
        f = features.Features.__new__(features.Features)
        f.cfg = {'image_api': {'model': 'wan2.6-t2i', 'group_daily_limit': 20}}
        f.index = [{'sha': 'x'}]
        f.s = type('S', (), {'state': {'image_usage': {'day': __import__('time').strftime('%Y-%m-%d'), 'group_count': 7},
                                       'web_usage': {'day': __import__('time').strftime('%Y-%m-%d'), 'count': 2}},
                             'save': lambda self: None,
                             'context': type('C', (), {'get_all_stars': lambda self: []})()})()
        status = f.self_status()
        self.assertIn('7/20', status['drawing'])
        self.assertIn('2/40', status['search'])
        self.assertEqual(status['voice'], '未加载')
        self.assertIn('没有Shell', status['limits'])
        self.assertNotIn('key', str(status).lower())

    async def test_clock_context_carries_rhythm(self):
        social = main.Social.__new__(main.Social)
        social.state = {}
        text = social.clock_context('group')
        self.assertIn('你的时间状态', text)
        self.assertIn('北京时间', text)
