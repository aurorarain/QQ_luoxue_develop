"""Model choice comes from configuration and the authenticated event, never from chat text."""
import re

PREMIUM_COMMAND = '/精绘26'
MODELS = ('wan2.6-t2i', 'wanx2.0-t2i-turbo', 'wan2.2-t2i-flash')
DEFAULT_MODEL = 'wan2.6-t2i'
DEFAULT_SIZE = '1280*1280'
LEGACY_SIZE = '1024*1024'


def premium_request(text):
    return bool(re.match(r'^/精绘26(?:\s|$)', (text or '').strip()))


# ── 绘图意图 ────────────────────────────────────────────────────────────────
# 旧规则只认"画一张/画个/生成…图"，真实漏判过：
#   我想要沧月图片，画一个我看看 / 帮我画一只猫 / 来张壁纸
# 所以改成三类强信号（量词、祈使、英文动词）＋一类意图短语（要/来/生成…图），
# 再排除"动画/漫画/画风/截图"这类只是提到"画/图"的说法。
DRAW_QUANTIFIER = re.compile(r'[画繪绘]\s*(?:一?[张幅个只支副]|一下|下|一画|一次|几[张幅])')
DRAW_IMPERATIVE = re.compile(r'(?:帮我|给我|替我|帮忙|麻烦|请|能不能|可不可以)\s*[画繪绘]')
DRAW_OBJECT = re.compile(r'(?:想要|想看|看看|要|求|来|做|生成|出|整|搞)\s*(?:一?[张幅个])?\s*'
                         r'[^，。！？\n]{0,12}?(?:的)?\s*(?:图|图片|壁纸|头像|立绘|插画|同人图|表情包)')
DRAW_ENGLISH = re.compile(r'\b(?:draw|illustrate|imagine)\b', re.I)
DRAW_NEGATIVE = re.compile(r'动画|漫画|画风|画廊|画家|笔画|计划|规划|策划|刻画|画质|画饼|截图|视频')


def is_draw_request(text):
    """True when the message asks her to produce a picture, not merely mentions one."""
    value = str(text or '').strip()
    if not value:
        return False
    if DRAW_QUANTIFIER.search(value) or DRAW_IMPERATIVE.search(value) or DRAW_ENGLISH.search(value):
        return True
    if DRAW_NEGATIVE.search(value):
        return False
    return bool(DRAW_OBJECT.search(value))


def select_image_request(text, sender, owner, cfg=None):
    """Return (model, size, prompt).

    The model is read from private settings. Saying "用2.6" in chat changes nothing, and the
    premium command still requires the real owner, so text alone can never pick a paid model.
    """
    text = (text or '').strip()
    cfg = cfg if isinstance(cfg, dict) else {}
    prompt = text
    if premium_request(text):
        if str(sender) != str(owner):
            raise PermissionError('只有老大可以使用精绘指令。')
        prompt = text[len(PREMIUM_COMMAND):].strip()
        if not prompt:
            raise ValueError('格式：/精绘26 画面描述。')
    model = str(cfg.get('model') or DEFAULT_MODEL)
    if model not in MODELS:
        model = DEFAULT_MODEL
    size = str(cfg.get('size') or (DEFAULT_SIZE if model == 'wan2.6-t2i' else LEGACY_SIZE))
    return model, size, prompt
