"""Fish S2 delivery cues and voice-intent detection. No switch to a paid model."""
import re
from .output_guard import guard_output

# Voice intent: one implementation shared by the group reply path and the luoxue_voice plugin.
# 实测漏判过的说法：用语音喊我句老大 / 用语音撒娇撒娇（旧规则只认“说讲念读”，不认喊叫撒娇）。
NEGATION = re.compile(r'(?:不要|别|不用|不想|不需要|停止|关闭|关掉).{0,6}(?:语音|音频|录音|声音|出声|开口)')
IMPERATIVE = re.compile(r'^(?:你)?(?:给我)?(?:(?:用|发|来|整|弄)(?:一?[个条段句])?|一[个条段句])语音'
                        r'|^(?:你)?(?:给我)?说(?:一?句|句话)'
                        r'|^来(?:一?句|段)(?:话|语音)')
REQUEST_FORWARD = re.compile(r'(?:用|发|来|整|弄|给|要|听).{0,6}(?:语音|音频|录音|声音|嗓子|出声)')
REQUEST_BACKWARD = re.compile(r'(?:语音|音频|录音).{0,6}(?:发|回|说|来|整)')
CUE = re.compile(r'语音|音频|录音|声音|嗓子|出声|开口|念给|读给|说给.{0,8}听|听听.{0,8}(?:说|讲|声音|嗓子)|(?:说|讲).{0,8}听听')
ACTION = re.compile(r'说|讲|介绍|回答|回复|回我|念|读|来|发|听|开口|出声|喊|叫|骂|夸|哄|撒娇|祝|问|答|道|唱|朗诵')


def wants_voice_reply(text):
    """True only when the user actually asks her to speak out loud."""
    value = re.sub(r'\s+', '', (text or '').strip())
    if not value or value.startswith('/'):
        return False
    if NEGATION.search(value):
        return False
    if IMPERATIVE.search(value) or REQUEST_FORWARD.search(value) or REQUEST_BACKWARD.search(value):
        return True
    return bool(CUE.search(value) and ACTION.search(value))


def prepare_voice(text):
    text=guard_output(text)
    text=re.sub(r'\[表情:[^\]]+\]|\[at:\d+\]','',text)
    text=re.sub(r'[（(][^()（）]{0,30}[）)]','',text).strip()
    text=re.sub(r'\[(?!happy\]|sad\]|calm\]|sarcastic\]|excited\]|whispering\])[^\]]+\]','',text)
    if re.search(r'\[(?:happy|sad|calm|sarcastic|excited|whispering)\]',text):return text[:900]
    if any(x in text for x in ['晚安','睡吧','轻一点','悄悄']):cue='[calm]'
    elif any(x in text for x in ['难受','委屈','伤心','不开心']):cue='[sad]'
    elif any(x in text for x in ['太好了','好耶','开心','嘿嘿']):cue='[happy]'
    elif any(x in text for x in ['本公主','才不是','笨蛋']):cue='[sarcastic]'
    else:cue='[calm]'
    return cue+' '+text[:900]
