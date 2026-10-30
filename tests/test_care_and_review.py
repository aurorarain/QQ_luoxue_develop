import datetime as dt
import io
import time
import types
import unittest
from unittest.mock import AsyncMock

import test_boundaries  # noqa: F401  (installs astrbot stubs)
from test_boundaries import features
from luoxue_social import rhythm


def build(state=None, generate=None):
    f = features.Features.__new__(features.Features)
    f.s = types.SimpleNamespace(state=state if state is not None else {}, save=lambda: None,
                                generate=generate or AsyncMock(return_value=''))
    f.cfg = {}
    f.index = []
    f.tasks = set()
    return f


def png_bytes():
    from PIL import Image as PILImage
    buffer = io.BytesIO()
    PILImage.new('RGB', (900, 600), (120, 180, 220)).save(buffer, format='PNG')
    return buffer.getvalue()


class SelfReview(unittest.IsolatedAsyncioTestCase):
    async def test_review_is_stored_and_visible_in_context(self):
        class Provider:
            async def text_chat(self, **kwargs):
                self.kwargs = kwargs
                return types.SimpleNamespace(completion_text='一只蓝鲸在浅色海面上，居中构图，冷色调')
        provider = Provider()
        f = build(state={})
        f.s.context = types.SimpleNamespace(get_using_provider_async=AsyncMock(return_value=provider))
        record = {'prompt': '鲸鱼', 'model': 'wan2.6-t2i', 'generated': True, 'delivered': True, 'channel': 'private'}
        f.s.state['drawing_history'] = [record]
        await f.review_drawing(record, png_bytes())
        self.assertIn('蓝鲸', record['review'])
        self.assertTrue(provider.kwargs['image_urls'][0].startswith('data:image/jpeg;base64,'))
        self.assertIn('蓝鲸', f.drawing_context(True))
        self.assertEqual(f.s.state['review_usage']['count'], 1)

    async def test_review_failure_does_not_break_drawing(self):
        f = build(state={})
        f.s.context = types.SimpleNamespace(get_using_provider_async=AsyncMock(side_effect=RuntimeError('no provider')))
        record = {'prompt': 'x', 'channel': 'private'}
        f.s.state['drawing_history'] = [record]
        await f.review_drawing(record, png_bytes())
        self.assertNotIn('review', record)

    async def test_review_quota_and_garbage_image(self):
        f = build(state={'review_usage': {'day': time.strftime('%Y-%m-%d'), 'count': 15}})
        f.s.context = types.SimpleNamespace(get_using_provider_async=AsyncMock())
        record = {'prompt': 'x'}
        await f.review_drawing(record, png_bytes())
        self.assertNotIn('review', record)
        self.assertFalse(f.s.context.get_using_provider_async.await_count)


class NightCare(unittest.IsolatedAsyncioTestCase):
    NIGHT = dt.datetime(2026, 10, 30, 23, 30, tzinfo=rhythm.TZ)

    def test_ready_window_and_cooldowns(self):
        now = dt.datetime(2026, 10, 30, 23, 30, tzinfo=rhythm.TZ)
        f = build(state={'last_owner': time.time() - 3 * 3600})
        self.assertTrue(f.night_care_ready(now))
        self.assertFalse(f.night_care_ready(dt.datetime(2026, 10, 30, 22, 0, tzinfo=rhythm.TZ)))
        self.assertFalse(f.night_care_ready(dt.datetime(2026, 10, 30, 3, 0, tzinfo=rhythm.TZ)))
        f.s.state['last_owner'] = time.time() - 600
        self.assertFalse(f.night_care_ready(now))
        f.s.state['last_owner'] = time.time() - 12 * 3600
        self.assertFalse(f.night_care_ready(now))
        f.s.state['last_owner'] = time.time() - 3 * 3600
        f.s.state['last_proactive'] = time.time() - 3600
        self.assertFalse(f.night_care_ready(now))

    async def test_guilt_trip_text_is_rejected(self):
        f = build(generate=AsyncMock(return_value='你怎么还不回我，我等了你一整晚。'))
        f.s.state['last_owner'] = time.time() - 3 * 3600
        self.assertIsNone(await f.night_care(self.NIGHT))
        self.assertNotIn('night_care_day', f.s.state)

    async def test_gentle_line_is_returned_and_capped_daily(self):
        f = build(generate=AsyncMock(return_value='眼睛明天会抗议的，早点睡。'))
        f.s.state['last_owner'] = time.time() - 3 * 3600
        text = await f.night_care(self.NIGHT)
        self.assertEqual(text, '眼睛明天会抗议的，早点睡。')
        self.assertIn('night_care_day', f.s.state)
        self.assertIsNone(await f.night_care(self.NIGHT))
