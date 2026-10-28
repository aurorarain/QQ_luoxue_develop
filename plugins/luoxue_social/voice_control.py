"""Fish S2 square-bracket delivery cues. No switch to a paid model."""
import re

def prepare_voice(text):
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
