"""Idempotent AstrBot 4.29.3 reset hotfix; preserve initialization without tools."""
import ast
import shutil
import datetime
from pathlib import Path

OLD = '''        if tool_schema_mode == "skills_like":
            tool_set = self.req.func_tool
            if not tool_set:
                return
'''
NEW = '''        if tool_schema_mode == "skills_like" and self.req.func_tool:
            tool_set = self.req.func_tool
'''

def patched(source):
    if NEW in source:return source
    if source.count(OLD)!=1:raise RuntimeError('Unrecognized runner version; refusing patch')
    result=source.replace(OLD,NEW)
    ast.parse(result)
    return result

if __name__=='__main__':
    target=Path('/AstrBot/astrbot/core/agent/runners/tool_loop_agent_runner.py')
    source=target.read_text()
    result=patched(source)
    if result!=source:
        backup=Path('/AstrBot/data/social_backups')/('runner-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        backup.mkdir(parents=True,exist_ok=False)
        shutil.copy2(target,backup/target.name)
        target.write_text(result)
    print('runner reset patch ready')
