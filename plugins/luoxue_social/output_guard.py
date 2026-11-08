"""Never forward a model's attempted command/tool serialization to QQ or speech."""
import re

CODE_FENCE = re.compile(r'```[a-zA-Z0-9_+-]*\s*\n?(.*?)```', re.S)


def _strip_fences(text):
    """模型爱把整段话包进 ```text，这里把围栏去掉只留内容。"""
    value = CODE_FENCE.sub(lambda m: m.group(1).strip(), text or '')
    value = value.replace('```', '')
    return value.strip()


def guard_output(text):
    if re.search(r'DSML|astrbot_execute_(?:shell|python)|<tool_call>|<function_calls>|```(?:bash|sh|powershell|cmd|shell)\b|^\s*(?:mkdir|sudo|docker|pip install|apt install|rm -|curl https?://|ssh\s|powershell\s)',text,re.I|re.M):
        return '环境和配置操作由老大处理，我不会执行或把内部命令当消息发出来。'
    return _strip_fences(text)
