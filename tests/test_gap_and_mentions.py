import asyncio
import pathlib
import types
import unittest
from unittest.mock import AsyncMock, patch

import test_boundaries  # noqa: F401
from test_boundaries import features
from astrbot.api.message_components import At, Plain


ROSTER = [{'qq': '90001', 'name': '西洲'}, {'qq': '90002', 'name': '昔泠'}, {'qq': '90003', 'name': '路人'}]


def build(roster=None, cfg=None):
    f = features.Features.__new__(features.Features)
    f.roster_cache = roster if roster is not None else list(ROSTER)
    f.cfg = cfg or {}
    f.s = types.SimpleNamespace(state={}, save=lambda: None)
    f.index = []
    f.library = pathlib.Path('/not-used')
    f.index_path = pathlib.Path('/not-used.json')
    f.choose_meme = lambda *a, **k: None
    f._last_out = {}
    f.reply_gap = True
    return f


class SendGap(unittest.IsolatedAsyncioTestCase):
    async def test_text_gap_is_five_seconds(self):
        f = build()
        f._last_out['s'] = __import__('time').time()
        with patch('luoxue_social.features.asyncio.sleep', AsyncMock()) as sleep:
            await f.send_gap('s', media=False)
        wait = sleep.await_args.args[0]
        self.assertGreaterEqual(round(wait), 4)
        self.assertLessEqual(round(wait), 5)

    async def test_media_gap_is_ten_seconds(self):
        f = build()
        f._last_out['s'] = __import__('time').time()
        with patch('luoxue_social.features.asyncio.sleep', AsyncMock()) as sleep:
            await f.send_gap('s', media=True)
        self.assertGreaterEqual(round(sleep.await_args.args[0]), 9)

    async def test_first_message_does_not_wait(self):
        f = build()
        with patch('luoxue_social.features.asyncio.sleep', AsyncMock()) as sleep:
            await f.send_gap('fresh', media=False)
        sleep.assert_not_awaited()

    async def test_configured_values_win(self):
        f = build(cfg={'reply_gap_text_seconds': 1, 'reply_gap_media_seconds': 2})
        f._last_out['s'] = __import__('time').time()
        with patch('luoxue_social.features.asyncio.sleep', AsyncMock()) as sleep:
            await f.send_gap('s', media=True)
        self.assertLess(sleep.await_args.args[0], 2.5)


class MentionResolution(unittest.TestCase):
    def test_resolves_the_reported_request(self):
        found = build().requested_mentions('@洛雪 帮我@一下西洲和昔，叫他们出来')
        self.assertEqual([qq for _, qq in found], ['90001', '90002'])

    def test_plain_chat_about_someone_does_not_resolve(self):
        self.assertEqual(build().requested_mentions('@洛雪 西洲今天好安静'), [])

    def test_no_names_found_returns_empty(self):
        self.assertEqual(build().requested_mentions('@洛雪 帮我@一下不存在的人，叫出来'), [])

    def test_bare_names_become_real_mentions_and_text_is_cleaned(self):
        f = build()
        event = types.SimpleNamespace(get_message_str=lambda: '@洛雪 帮我@一下西洲和昔，叫他们出来')
        chain = [Plain('西洲、昔，出来一下。')]
        result = f.ensure_requested_mentions(event, chain)
        mentions = [c for c in result if isinstance(c, At)]
        self.assertEqual([str(m.qq) for m in mentions], ['90001', '90002'])
        text = ''.join(c.text for c in result if isinstance(c, Plain))
        self.assertNotIn('西洲', text)
        self.assertNotIn('昔泠', text)

    def test_existing_marker_is_left_alone(self):
        f = build()
        event = types.SimpleNamespace(get_message_str=lambda: '帮我@西洲')
        chain = [At(qq='90001'), Plain('出来')]
        self.assertEqual(f.ensure_requested_mentions(event, chain), chain)
