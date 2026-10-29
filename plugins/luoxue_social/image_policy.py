"""Premium selection is determined by the authenticated incoming event, never LLM text."""
import re

PREMIUM_COMMAND='/精绘26'

def premium_request(text):
    return bool(re.match(r'^/精绘26(?:\s|$)',(text or '').strip()))

def select_image_request(text,sender,owner):
    text=(text or '').strip()
    if premium_request(text):
        if str(sender)!=str(owner):raise PermissionError('只有老大可以使用精绘指令。')
        prompt=text[len(PREMIUM_COMMAND):].strip()
        if not prompt:raise ValueError('格式：/精绘26 画面描述，仅本张使用2.6。')
        return 'wan2.6-t2i','1280*1280',prompt
    return 'wanx2.0-t2i-turbo','1024*1024',text
