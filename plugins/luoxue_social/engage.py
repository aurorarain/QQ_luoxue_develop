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



CN_DIGITS = {'零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
             '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}


def normalize_times(text):
    """把 '七点半' '十点' 这类中文时间换成数字，方便正则解析。"""
    import re as _re
    value = str(text or '')

    def fix(match):
        raw = match.group(1)
        hour = 0
        if raw == '十':
            hour = 10
        elif raw.startswith('十'):
            hour = 10 + CN_DIGITS.get(raw[1:], 0)
        elif raw.endswith('十'):
            hour = CN_DIGITS.get(raw[0], 0) * 10
        elif len(raw) == 2:
            hour = CN_DIGITS.get(raw[0], 0) * 10 + CN_DIGITS.get(raw[1], 0)
        else:
            hour = CN_DIGITS.get(raw, 0)
        return '%d点' % hour

    value = _re.sub(r'([一二两三四五六七八九十]{1,2})点(?=[半刻]|[^\u4e00-\u9fa5]|$)', fix, value)
    value = _re.sub(r'([一二两三四五六七八九十])(?=\s*(?:分钟|分)后)', lambda m: str(CN_DIGITS.get(m.group(1), 0)), value)
    value = _re.sub(r'([一二两三四五六七八九十])(?=\s*个?小时)', lambda m: str(CN_DIGITS.get(m.group(1), 0)), value)
    value = value.replace('半小时', '30分钟')
    return value

REL = re.compile(r'(?:(\d{1,3})\s*(?:分钟|分)后|(\d{1,2})\s*(?:个)?(?:小时|钟头)后)')
CLOCK = re.compile(r'(?:(今天|明天|后天|今晚|明早|明晚|早上|上午|中午|下午|傍晚|晚上|凌晨)?\s*(\d{1,2})[:：](\d{2})|(今天|明天|后天|今晚|明早|明晚|早上|上午|中午|下午|傍晚|晚上|凌晨)?\s*(\d{1,2})\s*点\s*([半一刻]{0,2}))')


def parse_reminder(text, now=None):
    """Very small parser: '20分钟后…' / '今天18:30…' / '明天9点…'. Returns due timestamp or None."""
    import datetime as dt
    from .rhythm import TZ
    current = now or dt.datetime.now(TZ)
    value = normalize_times(text or '')
    match = REL.search(value)
    if match:
        base = current.timestamp()
        if match.group(1):
            return base + int(match.group(1)) * 60
        return base + int(match.group(2)) * 3600
    match = CLOCK.search(value)
    if not match:
        return None
    day_word = match.group(1) or match.group(4) or ''
    offset = {'今天': 0, '今晚': 0, '明天': 1, '明早': 1, '明晚': 1, '后天': 2}.get(day_word, 0)
    explicit_day = day_word in ('今天', '今晚', '明天', '明早', '明晚', '后天')
    if match.group(2):
        hour, minute = int(match.group(2)), int(match.group(3))
    else:
        hour, minute = int(match.group(5)), 0
        tail = match.group(6) or ''
        if '半' in tail:
            minute = 30
        elif '一刻' in tail:
            minute = 15
        elif '三刻' in tail:
            minute = 45
    # 时段词调整 24 小时制
    if day_word in ('明早', '早上', '上午', '凌晨') and hour == 12:
        hour = 0
    if day_word in ('下午', '傍晚', '晚上', '今晚', '明晚') and hour < 12:
        hour += 12
    if day_word == '中午' and hour < 11:
        hour += 12
    target = (current + dt.timedelta(days=offset)).replace(hour=hour % 24, minute=minute, second=0, microsecond=0)
    # 没写具体哪天、或者写了"今天"但时间已过 → 顺延到明天
    if target <= current and (not explicit_day or offset == 0):
        target += dt.timedelta(days=1)
    return target.timestamp()


def parse_reminders(text, now=None):
    """一句话里可能有多个时间：'7点和9点'、'七点半、九点'、'20分钟后 和 明早8点'。"""
    import re as _re
    value = str(text or '')
    parts = [part for part in _re.split(r'[、，,；;]|和|还有|以及|再', value) if part.strip()]
    found = []
    for part in parts or [value]:
        due = parse_reminder(part, now)
        if due and due not in found:
            found.append(due)
    if not found:
        due = parse_reminder(value, now)
        if due:
            found.append(due)
    return found
