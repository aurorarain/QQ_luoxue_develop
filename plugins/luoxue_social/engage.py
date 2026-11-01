"""Chime-in scoring, song picking and reminder parsing.

Kept separate from features.py so the rules are easy to read and test.
"""
import re
import time

# 群聊插话的基础概率：没人点名时，绝大多数消息都不该被打断。
BASE = 0.02
# 提到她自己 / 提到主人时显著提高；只是普通话题时保持很低。
SELF_HINT = re.compile(r'洛雪|小洛雪|肥鱼')
OWNER_HINT = re.compile(r'主人|老大|群主')
QUESTION = re.compile(r'你(?:觉得|说|呢|看)|是不是|为什么|怎么会|谁|有没有|能不能')
LAUGH = re.compile(r'哈哈|笑死|草|绝了|离谱|太好笑')
SERIOUS = re.compile(r'难受|焦虑|失眠|压力|难受|分手|辞职|生病|难受|急|求助|报警|医院')
SKIP_TOPICS = re.compile(r'^/@|^http')


def chime_score(text):
    """0 表示绝不插话；越高越可能。返回 (score, reason)。"""
    value = (text or '').strip()
    if len(value) < 4 or SKIP_TOPICS.search(value):
        return 0.0, 'too_short_or_link'
    if SERIOUS.search(value):
        return 0.0, 'serious'
    score = BASE
    reasons = ['base']
    if SELF_HINT.search(value):
        score += 0.55
        reasons.append('self')
    if OWNER_HINT.search(value):
        score += 0.35
        reasons.append('owner')
    if QUESTION.search(value):
        score += 0.06
        reasons.append('question')
    if LAUGH.search(value):
        score += 0.08
        reasons.append('laugh')
    return min(score, 0.75), '+'.join(reasons)


def should_try(score, rng):
    return score > 0 and rng.random() <= score


AUDIO_EXT = ('.mp3', '.wav', '.flac', '.m4a', '.ogg')


def pick_song(directory, name=''):
    """Pick a local audio file; never downloads anything."""
    import pathlib
    root = pathlib.Path(directory)
    if not root.is_dir():
        return None
    files = [p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in AUDIO_EXT]
    if not files:
        return None
    name = (name or '').strip()
    if name:
        hits = [p for p in files if name in p.stem]
        if hits:
            return hits[0]
    return sorted(files)[0]


REL = re.compile(r'(?:(\d{1,3})\s*(?:分钟|分)后|(\d{1,2})\s*(?:小时|钟头)后)')
CLOCK = re.compile(r'(?:(今天|明天|后天)?\s*(\d{1,2})[:：](\d{2})|(今天|明天|后天)\s*(\d{1,2})\s*点(?:半)?)')


def parse_reminder(text, now=None):
    """Very small parser: '20分钟后…' / '今天18:30…' / '明天9点…'. Returns due timestamp or None."""
    import datetime as dt
    from .rhythm import TZ
    current = now or dt.datetime.now(TZ)
    value = text or ''
    match = REL.search(value)
    if match:
        base = current.timestamp()
        if match.group(1):
            return base + int(match.group(1)) * 60
        return base + int(match.group(2)) * 3600
    match = CLOCK.search(value)
    if not match:
        return None
    day_word = match.group(1) or match.group(4) or '今天'
    offset = {'今天': 0, '明天': 1, '后天': 2}.get(day_word, 0)
    if match.group(2):
        hour, minute = int(match.group(2)), int(match.group(3))
    else:
        hour, minute = int(match.group(5)), 0
    target = (current + dt.timedelta(days=offset)).replace(hour=hour % 24, minute=minute, second=0, microsecond=0)
    if day_word == '今天' and target <= current:
        target += dt.timedelta(days=1)
    return target.timestamp()
