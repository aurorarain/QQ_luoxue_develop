"""Run on the server AFTER backups. Private data never enters this repository."""
import ast
import datetime
import json
import pathlib
import re
import shutil

ROOT=pathlib.Path('/opt/luoxue/astrbot/data')
backup=ROOT/'social_backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True,exist_ok=True)
config=ROOT/'cmd_config.json';shutil.copy2(config,backup/config.name)
c=json.loads(config.read_text(encoding='utf-8-sig'))
settings=json.loads((ROOT/'config/luoxue_social_settings.json').read_text(encoding='utf-8-sig'))
owner=str(settings['owner_qq']);group=str(settings['group_qq'])
c['admins_id']=[owner]
c['disable_builtin_commands']=True # QQ-side plugin/config administration is intentionally disabled.
c['platform_settings'].update(enable_id_white_list=True,id_whitelist=[group,'napcat:FriendMessage:'+owner],
    wl_ignore_admin_on_group=False,wl_ignore_admin_on_friend=True,ignore_bot_self_message=True,ignore_at_all=True)
for role in ('admin','member'):
    c['provider_settings']['computer_use_local_permissions'][role]={'allow_execution':False,'allow_network':False,'filesystem_scope':'workspace'}
c['provider_settings']['computer_use_require_admin']=True
c['provider_settings']['proactive_capability']={'add_cron_tools':False}
config.write_text(json.dumps(c,ensure_ascii=False,indent=2))

voice=ROOT/'plugins/luoxue_voice/main.py'
if voice.exists():
    shutil.copy2(voice,backup/'voice-main.py')
    t=voice.read_text()
    if '# LUOXUE_EMOTION_V2' not in t:
        t=t.replace('"text": text,','"text": __import__("data.plugins.luoxue_social.voice_control", fromlist=["prepare_voice"]).prepare_voice(text), # LUOXUE_EMOTION_V2')
    # Route owner natural voice replies through the normal social observation/injection boundary.
    t=re.sub(r'str\(event.get_sender_id\(\)\) == [\"\x27]\d+[\"\x27]', 'str(event.get_sender_id()) == '+repr(owner),t)
    voice.write_text(t)

memory=ROOT/'plugins/astrbot_plugin_memory/main.py'
if memory.exists():
    shutil.copy2(memory,backup/'memory-main.py');t=memory.read_text()
    if '# LUOXUE_MEMORY_SCOPE_V2' not in t:
        lines=t.splitlines(keepends=True);insertions=[]
        for node in ast.walk(ast.parse(t)):
            if not isinstance(node,ast.AsyncFunctionDef):continue
            decorators=[ast.get_source_segment(t,d) or '' for d in node.decorator_list]
            tool=any('llm_tool' in d for d in decorators)
            inject=node.name=='inject_memory'
            if not (tool or inject):continue
            body=node.body
            pos=body[1].lineno-1 if isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str) and len(body)>1 else body[0].lineno-1
            reply="return '只有Alex的私聊可维护持久记忆或人设。'" if tool else 'return'
            guard='        # LUOXUE_MEMORY_SCOPE_V2\n        if not event.is_private_chat() or str(event.get_sender_id()) != '+repr(owner)+':\n            '+reply+'\n'
            insertions.append((pos,guard))
        for pos,guard in sorted(insertions,reverse=True):lines.insert(pos,guard)
        memory.write_text(''.join(lines))

qdir=ROOT/'plugins/astrbot_plugin_qzone';q=qdir/'main.py'
if q.exists():
    shutil.copy2(q,backup/'qzone-main.py');t=q.read_text();lines=t.splitlines(keepends=True);remove=set()
    for n in ast.walk(ast.parse(t)):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for d in n.decorator_list:
                if 'filter.' in (ast.get_source_segment(t,d) or ''):remove.update(range(d.lineno-1,d.end_lineno))
    q.write_text(''.join(x for i,x in enumerate(lines) if i not in remove))
    p=ROOT/'config/astrbot_plugin_qzone_config.json'
    if p.exists():
        value=json.loads(p.read_text(encoding='utf-8-sig'));value['trigger'].update(publish_cron='',comment_cron='',read_prob=0,like_when_comment=False)
        p.write_text(json.dumps(value,ensure_ascii=False,indent=2))
for p in [voice,memory,q,ROOT/'plugins/luoxue_social/main.py']:
    if p.exists():ast.parse(p.read_text())
print('patched with backups:',backup)
