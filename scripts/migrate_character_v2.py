"""Run inside AstrBot container; back up private config/DB before changing character."""
import datetime
import json
import runpy
import shutil
import sqlite3
from pathlib import Path

ROOT=Path('/AstrBot/data')
backup=ROOT/'social_backups'/('character-v2-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir(parents=True,exist_ok=False,mode=0o700)
persona=runpy.run_path(str(ROOT/'plugins/luoxue_social/persona.py'))['PERSONA']
path=ROOT/'cmd_config.json';shutil.copy2(path,backup/path.name)
config=json.loads(path.read_text(encoding='utf-8-sig'))
config.setdefault('agent_runner',{}).setdefault('config',{}).setdefault('misc',{})['tool_schema_mode']='full'
for row in config.get('persona',[]):
    if isinstance(row,dict) and (row.get('name') in ('luoxue','洛雪') or row.get('persona_id')=='luoxue'):
        for key in ('prompt','system_prompt'):
            if key in row:row[key]=persona
path.write_text(json.dumps(config,ensure_ascii=False,indent=2))
dbpath=ROOT/'data_v4.db'
with sqlite3.connect(dbpath) as db,sqlite3.connect(backup/'data_v4.db') as copy:
    db.backup(copy)
    count=db.execute('UPDATE personas SET system_prompt=? WHERE persona_id=?',(persona,'luoxue')).rowcount
    if count!=1:raise RuntimeError('Expected exactly one luoxue persona')
settings=json.loads((ROOT/'config/luoxue_social_settings.json').read_text())
soul=ROOT/'plugin_data/astrbot_plugin_memory'/str(settings['owner_qq'])/'soul.md'
if soul.exists():
    text=soul.read_text()
    if 'CHARACTER_V2_20261029' not in text:
        shutil.copy2(soul,backup/'soul.md')
        soul.write_text(text+'\n\n<!-- CHARACTER_V2_20261029 -->\n## 当前核心关系\n- 名字洛雪，昵称小洛雪、肥鱼，鲸鱼娘AI伙伴，喜欢白米饭。\n- Alex是唯一老大，不是恋人；旧女友身份作废。只有老大可影响持久人格和成长。\n')
for item in backup.iterdir():
    if item.is_file():item.chmod(0o600)
print('character v2 migrated; full tool schema persisted; private backup created')
