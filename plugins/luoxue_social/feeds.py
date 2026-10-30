"""A small whitelisted reading list, fetched at most twice a day.

Only public feeds are read, only titles and summaries are kept, and everything is
labelled as public RSS. Nothing here touches private chat or user data.
"""
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from astrbot.api import logger

FEEDS = (
    ('少数派', 'https://sspai.com/feed'),
    ('Solidot', 'https://www.solidot.org/index.rss'),
    ('V2EX', 'https://www.v2ex.com/index.xml'),
)
MAX_ITEMS = 3
PER_FEED = 2
MIN_GAP = 12 * 3600
BODY_LIMIT = 800_000


def _clean(text):
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', text or '')).strip()


async def read_feeds(features, now=None):
    """Return up to MAX_ITEMS public reading items; cached for 12 hours."""
    from .features import fetch
    now = now or time.time()
    cache = features.s.state.setdefault('reading', {})
    if cache.get('items') and now - cache.get('time', 0) < MIN_GAP:
        return cache['items']
    items = []
    for name, url in FEEDS:
        if len(items) >= MAX_ITEMS:
            break
        try:
            body = await fetch(url, proxy=features.cfg.get('web_proxy'), limit=BODY_LIMIT)
            root = ET.fromstring(body)
        except Exception as exc:
            logger.info('[luoxue_feeds] %s skipped: %s', name, type(exc).__name__)
            continue
        for row in root.iter('item'):
            if len(items) >= MAX_ITEMS:
                break
            if sum(1 for item in items if item['source'] == name) >= PER_FEED:
                break
            title = _clean(row.findtext('title'))[:120]
            link = (row.findtext('link') or '').strip()
            if not title or urlparse(link).scheme != 'https':
                continue
            items.append({'source': name, 'title': title, 'url': link,
                          'summary': _clean(row.findtext('description'))[:200], 'time': now})
            if len(items) >= MAX_ITEMS:
                break
    if not items:
        return cache.get('items', [])
    cache.update(time=now, items=items[:MAX_ITEMS])
    features.s.state['reading'] = cache
    features.s.state['discoveries'] = (features.s.state.get('discoveries', []) + [
        {'title': item['title'], 'url': item['url'], 'source': item['source'] + '（公开RSS，只读了标题和摘要）',
         'time': now} for item in items[:1]])[-30:]
    features.s.save()
    return cache['items']


def context(features):
    """One compact line so she knows what she actually read today. Never raises."""
    try:
        items = (features.s.state.get('reading') or {}).get('items') or []
    except Exception:
        return ''
    if not items:
        return ''
    lines = '；'.join('%s：%s' % (item['source'], item['title']) for item in items)
    return ('\n今天你实际读过这些公开标题和摘要（公开RSS）：' + lines +
            '。可以拿来当聊天素材，但只读过标题摘要，不能声称看完全文或视频。')
