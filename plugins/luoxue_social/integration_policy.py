"""Boundaries shared by reviewed third-party plugin adapters."""
import json
import os
import re
from pathlib import Path


def ids():
    path = Path(os.getenv('LUOXUE_SETTINGS', '/AstrBot/data/config/luoxue_social_settings.json'))
    data = json.loads(path.read_text()) if path.exists() else {}
    return str(data.get('owner_qq', '')), str(data.get('group_qq', ''))


def owner_private(event):
    owner, _ = ids()
    return bool(owner and event.is_private_chat() and str(event.get_sender_id()) == owner)


def allowed_channel(event):
    _, group = ids()
    return owner_private(event) or bool(group and not event.is_private_chat() and str(event.get_group_id()) == group)


def public_query(value):
    return bool(value and len(value) <= 2000 and not re.search(
        r'密码|验证码|私钥|api.?key|sk-[\w-]+|银行卡|身份证|家庭住址|电话号码', value, re.I))


def allowed_tool_call(event, name, arguments):
    if not owner_private(event):
        return False
    if name in {'poke_user', 'qts_poke_user'}:
        return str(arguments.get('qq_id', '')) == ids()[0]
    if name in {'delete_message', 'qts_delete_message'}:
        return bool(re.search(r'撤回|删除.{0,6}消息', event.get_message_str() or ''))
    if name.startswith('anysearch_'):
        return public_query(json.dumps(arguments, ensure_ascii=False))
    return True
