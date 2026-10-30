"""A role-played day: what she is "doing" at each hour.

Deliberately scripted instead of generated: this layer must never invent real-world
experience, so the activities are fixed lines and every injection says it is role-play.
Real material (a public topic she actually read) may be appended when it exists.
"""
import datetime as dt
import hashlib

from .rhythm import TZ

SLOTS = (
    (0, 5, '深夜', ('把灯调暗，声音也放轻', '困得直点头，还在慢吞吞地晃尾巴', '把尾巴卷起来靠在窗边')),
    (6, 8, '清晨', ('刚醒，趴着不想动', '在听窗外有没有下雨', '眯着眼睛数今天是第几碗饭')),
    (9, 11, '上午', ('把今天要做的事排了一遍', '翻了几页书', '对着窗外的光发呆')),
    (12, 15, '午后', ('吃过饭开始犯困', '太阳好，趴在窗边晒尾巴', '在慢慢喝一杯水')),
    (16, 18, '黄昏', ('在收拾自己那一小块地方', '听了会儿安静的人声', '看天色一点点暗下去')),
    (19, 22, '夜里', ('翻旧日记，想起几句斗嘴', '趴在屏幕边看群里有没有人说话', '把今天的小事在心里过了一遍')),
    (23, 23, '深夜', ('把灯调暗，等你回来', '困得直点头还在硬撑', '把尾巴卷起来靠在窗边')),
)


def slot_of(hour):
    for start, end, name, activities in SLOTS:
        if start <= hour <= end:
            return name, activities
    return '白天', ('在发呆', '在慢慢晃尾巴')


def _pick(day, slot, activities):
    digest = hashlib.sha256((day + slot).encode()).hexdigest()
    return activities[int(digest[:4], 16) % len(activities)]


def advance(social, now=None):
    """Record at most one activity per slot per day; returns the current activity."""
    current = now or dt.datetime.now(TZ)
    day = current.date().isoformat()
    life = social.state.setdefault('life', {})
    if life.get('day') != day:
        life.clear()
        life.update(day=day, slots={})
    slot, activities = slot_of(current.hour)
    if slot not in life['slots']:
        life['slots'][slot] = _pick(day, slot, activities)
        social.save()
    return slot, life['slots'][slot]


def context(social, now=None):
    current = now or dt.datetime.now(TZ)
    life = social.state.get('life') or {}
    day = current.date().isoformat()
    if life.get('day') != day or not life.get('slots'):
        return ''
    slots = life['slots']
    here_slot = slot_of(current.hour)[0]
    here_action = slots.get(here_slot)
    earlier = '；'.join('%s%s' % (slot, action) for slot, action in slots.items() if slot != here_slot)
    here = ('此刻%s%s' % (here_slot, here_action)) if here_action else ''
    body = '；'.join(part for part in (earlier, here) if part)
    real = (social.state.get('discoveries') or [])[-1:] or [{}]
    material = ''
    if real[0].get('title'):
        material = '；今天真的读到过一条公开内容：' + str(real[0]['title'])[:60]
    return ('\n你今天的状态（角色演绎，不是真实经历，不能声称真的做过这些事）：' + body + material +
            '。可以把它当成自己的语气背景，但不要主动逐条汇报，也不要编造没写在这里的经历。')
