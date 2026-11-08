"""刷贴吧：一次真正的"逛"，不是看一眼就完。

流程参考 Generative Agents 的记忆流设计（重要性/相关性/时近性打分）：
1) 先扫一屏标题（20~30 条）
2) 按"她自己的兴趣 + 好奇 + 新鲜度"给标题打分
3) 只有超过阈值的才点进去读正文，最多 3 篇
4) 读完按"信息量 + 情绪词 + 跟自己的相关度"算显著度
5) 显著度决定：记忆重要度、心情变化、兴趣权重增减、要不要跟人提
"""
import asyncio
import re
import time

# 情绪词表：只做粗分类，够用就行
POSITIVE = ('好', '喜欢', '开心', '笑', '可爱', '厉害', '爽', '香', '棒', '治愈', '温柔', '期待')
NEGATIVE = ('烦', '烂', '恶心', '气', '失望', '难受', '吵', '垃圾', '骂', '崩', '痛', '累')
CURIOUS = ('为什么', '怎么', '居然', '竟然', '能不能', '有没有', '求', '问', '?', '？')
EMOTIONAL = POSITIVE + NEGATIVE + CURIOUS

STOP = set('的了是在我你他她它们这那就都和与及一个什么怎么没什么这个那个')


def keywords(text, limit=8):
    """抽关键词：按非中文切段，每段取开头 2~4 字，避免拼出跨词的怪词。"""
    out = []
    for seg in re.split(r'[^\u4e00-\u9fa5]+', str(text or '')):
        seg = seg.strip()
        if len(seg) < 2:
            continue
        for size in (4, 3, 2):
            word = seg[:size]
            if word in STOP or word in out:
                continue
            out.append(word)
            break
        if len(out) >= limit:
            break
    return out[:limit]


def interest_of(state, word):
    return float((state.get('interests') or {}).get(word) or 0.0)


def title_score(state, title, mood=None):
    """标题打分：兴趣 0.45 + 好奇 0.25 + 新鲜 0.2 + 情绪词 0.1。"""
    interests = state.get('interests') or {}
    words = keywords(title)
    match = max([interest_of(state, w) for w in words] or [0.0])
    curiosity = 1.0 if any(c in title for c in CURIOUS) else 0.0
    seen = state.setdefault('browse_seen', {})
    novelty = 0.0 if title[:20] in seen else 1.0
    emotional = 1.0 if any(c in title for c in EMOTIONAL) else 0.0
    desire = float((mood or {}).get('desires', {}).get('见', 50)) / 100.0
    # 还没有兴趣画像时，给一点"什么都想看看"的底子
    base = 0.18 if not interests else 0.0
    score = (base + match * 0.45 + curiosity * 0.25 + novelty * 0.2 + emotional * 0.1) * (0.6 + 0.6 * desire)
    return round(score, 3), words, match


def _clean_gist(text):
    body = str(text or '')
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if lines and lines[0].startswith('标题'):
        lines = lines[1:]
    return ' / '.join(lines)[:150]


def salience(text, match, words):
    """读完之后算这件事有多重要。"""
    length = min(1.0, len(text) / 800.0)
    emotion_hits = sum(1 for c in EMOTIONAL if c in text)
    emotion = min(1.0, emotion_hits / 6.0)
    relevance = min(1.0, match * 1.2)
    # 她愿意点进去本身说明有点兴趣，给个底
    score = 0.15 + 0.35 * length + 0.3 * emotion + 0.35 * relevance
    return round(max(0.2, min(0.85, score)), 2)


def apply_effects(social, forum, opened, scanned, skipped):
    """把这次"逛"的后果落到她身上：记忆、心情、兴趣、想说的话。"""
    state = social.state
    features = social.features
    now = time.time()
    interests = state.setdefault('interests', {})
    seen = state.setdefault('browse_seen', {})
    total_salience = 0.0
    mentions = []

    for item in opened:
        title = item['title']
        body = item.get('excerpt', '')
        words = item.get('words') or keywords(title)
        for word in words[:3]:
            interests[word] = round(min(3.0, interest_of(state, word) + 0.12), 2)
        for word in (item.get('body_words') or keywords(body))[:3]:
            interests[word] = round(min(3.0, interest_of(state, word) + 0.06), 2)
        seen[title[:20]] = now
        total_salience += item['salience']
        features.remember(
            '在「%s」吧看到《%s》：%s' % (forum, title, body[:160]),
            '洛雪·刷贴吧', imp=item['salience'], cat='event', role='洛雪')
        if item['salience'] >= 0.55:
            mentions.append(title)

    # 兴趣整体轻微衰减，旧词自然淡出
    for word in list(interests):
        interests[word] = round(interests[word] * 0.985, 3)
        if interests[word] < 0.02:
            interests.pop(word, None)

    if skipped:
        for word in skipped[:3]:
            interests[word] = round(max(0.0, interest_of(state, word) - 0.01), 2)

    # 心情：看过东西 = 满足"见"，内容有情绪就带着走一点
    wants = {'见': -min(30, 8 + 6 * len(opened))}
    features.apply_mood_deltas({'desires': wants})
    if total_salience >= 1.2:
        features.bump_emotion('喜', 6)
    if any(any(n in o.get('excerpt', '') for n in NEGATIVE) for o in opened):
        features.bump_emotion('怒', 4)
        features.bump_emotion('哀', 3)
    if any(any(p in o.get('excerpt', '') for p in POSITIVE) for o in opened):
        features.bump_emotion('喜', 5)

    # 想跟人说的东西先存着，等她自己决定要不要提
    queue = state.setdefault('browse_queue', [])
    for item in opened:
        if item['salience'] < 0.15:
            continue
        queue.append({'at': now, 'forum': forum, 'title': item['title'][:60],
                      'url': item.get('url', ''),
                      'gist': _clean_gist(item.get('excerpt', '')),
                      'salience': item['salience'], 'injected': 0, 'said': False})
    state['browse_queue'] = queue[-15:]

    sessions = state.setdefault('browse_sessions', [])
    sessions.append({
        'at': now, 'forum': forum, 'scanned': scanned,
        'opened': [{'title': o['title'], 'url': o.get('url', ''), 'salience': o['salience']}
                   for o in opened],
        'skipped': len(skipped), 'salience_total': round(total_salience, 2),
    })
    state['browse_sessions'] = sessions[-30:]
    if len(interests) > 200:
        top = sorted(interests.items(), key=lambda kv: kv[1], reverse=True)[:200]
        state['interests'] = dict(top)
    try:
        social.save()
    except Exception:
        pass
    return {'opened': len(opened), 'salience': round(total_salience, 2), 'mentions': mentions}


def pick_forum(social, fallback='原神'):
    """从她的兴趣里挑一个吧；没有就随机几个常看的。"""
    interests = social.state.get('interests') or {}
    forums = social.state.get('browse_forums') or ['原神', '贴吧', '猫', '电影', '音乐']
    if interests:
        best = max(forums, key=lambda f: interest_of(social.state, f))
        return best
    return forums[int(time.time()) % len(forums)]


async def run_session(social, forum=None, scan_limit=18, max_open=3, threshold=0.30):
    """执行一次完整的刷贴吧。"""
    from . import tieba
    forum = forum or pick_forum(social)
    if not tieba.node_status().get('online'):
        return {'ok': False, 'reason': 'offline'}

    listing = await asyncio.to_thread(tieba.read_forum, forum, limit=scan_limit)
    if not listing or '没读到' in listing or '安全验证' in listing:
        social.features.note_browse(forum, '贴吧/本地电脑', str(listing)[:200], False)
        return {'ok': False, 'reason': 'read_failed'}

    rows = []
    for line in str(listing).splitlines():
        line = line.strip()
        if 'http' not in line:
            continue
        head, sep, tail = line.partition('http')
        title = head.strip(' ·-—')
        if not title or len(title) < 2:
            continue
        url = (sep + tail).strip()
        if '/p/' not in url:
            continue
        rows.append({'title': title, 'url': url})

    mood = social.features.mood_snapshot()
    scored = []
    for row in rows[:scan_limit]:
        score, words, match = title_score(social.state, row['title'], mood)
        scored.append({**row, 'score': score, 'words': words, 'match': match})
    scored.sort(key=lambda x: x['score'], reverse=True)

    opened = []
    for item in scored[:max_open]:
        if item['score'] < threshold:
            continue
        detail = await asyncio.to_thread(tieba.read_thread, item['url'], limit=5)
        if not detail or any(marker in detail for marker in ('没解析', '打不开', '不是贴吧帖子', '安全验证')):
            continue
        opened.append({
            'title': item['title'], 'url': item['url'],
            'excerpt': str(detail)[:400], 'words': item['words'],
            'body_words': keywords(str(detail)),
            'salience': salience(str(detail), item['match'], item['words']),
        })

    skipped = [w for item in scored[max_open:max_open + 8] for w in item['words'][:2]]
    effects = apply_effects(social, forum, opened, len(scored), skipped)
    social.features.note_browse(
        forum, '贴吧/本地电脑',
        '扫了 %d 篇，点进 %d 篇：%s' % (len(scored), len(opened),
                                        '；'.join(o['title'][:20] for o in opened) or '都没兴趣'),
        True)
    return {'ok': True, 'forum': forum, 'scanned': len(scored), **effects}
