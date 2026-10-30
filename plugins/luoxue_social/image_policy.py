"""Model choice comes from configuration and the authenticated event, never from chat text."""
import re

PREMIUM_COMMAND = '/精绘26'
MODELS = ('wan2.6-t2i', 'wanx2.0-t2i-turbo', 'wan2.2-t2i-flash')
DEFAULT_MODEL = 'wan2.6-t2i'
DEFAULT_SIZE = '1280*1280'
LEGACY_SIZE = '1024*1024'


def premium_request(text):
    return bool(re.match(r'^/精绘26(?:\s|$)', (text or '').strip()))


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
