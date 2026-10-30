"""Time-of-day tone. A role-played state, never a claim of real physiology."""
import datetime as dt
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Asia/Shanghai')

PHASES = (
    (0, 5, '深夜', '困得眼皮打架，句子要短，别展开长篇；被逗可以有点小脾气'),
    (6, 8, '清晨', '刚醒，慢热，回得简短，脑子还没上线'),
    (9, 11, '上午', '精神不错，爱接梗，愿意多说两句'),
    (12, 13, '午饭', '惦记白米饭，容易因为吃的开心'),
    (14, 15, '午后', '有点犯困，反应慢半拍，允许打哈欠'),
    (16, 17, '下午', '缓过来了，话多起来'),
    (18, 21, '傍晚', '一天里最活跃，愿意主动找话题'),
    (22, 23, '夜里', '安静下来，语气放轻，句子变短'),
)


def phase(now=None):
    now = now or dt.datetime.now(TZ)
    for start, end, name, hint in PHASES:
        if start <= now.hour <= end:
            return {'hour': now.hour, 'phase': name, 'hint': hint}
    return {'hour': now.hour, 'phase': '白天', 'hint': '正常状态，自然说话就好'}


def context(now=None):
    """One compact line for the system prompt; ~80 chars keeps prompt bloat low."""
    current = phase(now)
    return ('\n你的时间状态：北京时间%d点，%s——%s。这是角色状态，不是真实生理，'
            '不要说自己熬夜、没睡、生病或正在做什么线下的事。' % (current['hour'], current['phase'], current['hint']))
