import types
import unittest
from unittest.mock import AsyncMock, patch

import test_boundaries  # noqa: F401
from test_boundaries import features
from luoxue_social import feeds

RSS = b'''<rss><channel>
<item><title>First public topic</title><link>https://example.org/a</link><description>alpha</description></item>
<item><title>Second public topic</title><link>https://example.org/b</link><description>beta</description></item>
<item><title>Unsafe link</title><link>http://example.org/c</link><description>gamma</description></item>
</channel></rss>'''


def build(state=None):
    f = features.Features.__new__(features.Features)
    f.s = types.SimpleNamespace(state=state if state is not None else {}, save=lambda: None)
    f.cfg = {}
    return f


class ReadingFeeds(unittest.IsolatedAsyncioTestCase):
    async def test_keeps_only_https_items_and_caps_count(self):
        f = build()
        with patch.object(features, 'fetch', AsyncMock(return_value=RSS)):
            items = await feeds.read_feeds(f)
        self.assertTrue(items)
        self.assertLessEqual(len(items), feeds.MAX_ITEMS)
        self.assertTrue(all(item['url'].startswith('https://') for item in items))
        self.assertTrue(all('RSS' in (d.get('source') or '') for d in f.s.state['discoveries']))

    async def test_cache_avoids_refetching_within_the_gap(self):
        f = build()
        fetch = AsyncMock(return_value=RSS)
        with patch.object(features, 'fetch', fetch):
            await feeds.read_feeds(f, now=1000)
            after_first = fetch.await_count
            await feeds.read_feeds(f, now=1000 + 3600)
        self.assertGreaterEqual(after_first, 1)
        self.assertEqual(fetch.await_count, after_first)

    async def test_failing_feed_is_tolerated(self):
        f = build()
        with patch.object(features, 'fetch', AsyncMock(side_effect=RuntimeError('blocked'))):
            items = await feeds.read_feeds(f)
        self.assertEqual(items, [])
        self.assertEqual(feeds.context(f), '')

    async def test_context_labels_reading_as_titles_only(self):
        f = build({'reading': {'time': 1, 'items': [{'source': '少数派', 'title': '某个公开标题', 'url': 'https://x'}]}})
        text = feeds.context(f)
        self.assertIn('某个公开标题', text)
        self.assertIn('不能声称看完全文或视频', text)

    async def test_sources_are_mixed_instead_of_one_feed_filling_the_list(self):
        f = build()
        feeds_in = (('A源', 'https://a.example/feed'), ('B源', 'https://b.example/feed'))

        async def fake_fetch(url, **kwargs):
            name = 'A' if 'a.example' in url else 'B'
            return RSS.replace(b'example.org', (name.lower() + '.example').encode())

        with patch.object(feeds, 'FEEDS', feeds_in), patch.object(features, 'fetch', AsyncMock(side_effect=fake_fetch)):
            items = await feeds.read_feeds(f)
        self.assertEqual({item['source'] for item in items}, {'A源', 'B源'})
        self.assertLessEqual(max(sum(1 for i in items if i['source'] == s) for s in ('A源', 'B源')), feeds.PER_FEED)

    async def test_no_reading_means_no_context(self):
        self.assertEqual(feeds.context(build()), '')
