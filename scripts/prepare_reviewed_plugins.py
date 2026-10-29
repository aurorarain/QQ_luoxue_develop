"""Prepare licensed upstream plugins with narrow event/tool adapters, outside this repo.

Usage: python prepare_reviewed_plugins.py SOURCE_ROOT OUTPUT_ROOT
Original code and licenses remain in each installed plugin, not vendored here.
"""
import ast
import json
import pathlib
import shutil
import sys

NAMES = ('astrbot_plugin_anysearch', 'astrbot_plugin_qqprofile_ex',
         'astrbot_plugin_parser', 'astrbot_plugin_qq_tools', 'astrbot_plugin_relationship')
POLICY = 'from data.plugins.luoxue_social.integration_policy import '


def inject_functions(path, selector, guard):
    text = path.read_text(encoding='utf-8-sig')
    edits = []
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.AsyncFunctionDef) or not selector(node):
            continue
        body = node.body
        offset = 1 if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str) else 0
        pos = body[offset].lineno - 1
        indent = ' ' * body[offset].col_offset
        edits.append((pos, '\n'.join(indent + line for line in guard(node)) + '\n'))
    lines = text.splitlines(keepends=True)
    for pos, code in sorted(edits, reverse=True):
        lines.insert(pos, code)
    output = ''.join(lines)
    ast.parse(output)
    path.write_text(output, encoding='utf-8')


def prepare(source_root, output_root):
    source_root, output_root = pathlib.Path(source_root), pathlib.Path(output_root)
    for name in NAMES:
        target = output_root / name
        shutil.copytree(source_root / name, target, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        main = target / 'main.py'
        if name in {'astrbot_plugin_qqprofile_ex', 'astrbot_plugin_relationship'}:
            # WebUI routes stay under AstrBot authentication. Chat hooks/commands only see owner-private events.
            inject_functions(main,
                lambda n: any(a.arg == 'event' for a in n.args.args) and bool(n.decorator_list),
                lambda n: [POLICY + 'owner_private', 'if not owner_private(event):', '    return'])
        if name == 'astrbot_plugin_qqprofile_ex':
            # No plugin-driven persona switching; growth remains in the existing owner-only memory layer.
            text = main.read_text()
            tree = ast.parse(text);lines=text.splitlines(keepends=True);remove=set()
            for n in ast.walk(tree):
                if isinstance(n, ast.AsyncFunctionDef) and any('切换人格' in ast.get_source_segment(text,d) for d in n.decorator_list):
                    for d in n.decorator_list:remove.update(range(d.lineno-1,d.end_lineno))
            main.write_text(''.join(l for i,l in enumerate(lines) if i not in remove),encoding='utf-8')
        if name == 'astrbot_plugin_parser':
            inject_functions(main, lambda n: n.name == 'llm_parse_media_url',
                lambda n: [POLICY + 'owner_private', 'if not owner_private(event):',
                           "    return '仅主人私聊可调用解析工具；群内可直接分享支持的链接。'"])
            inject_functions(main, lambda n: n.name == 'on_message',
                lambda n: [POLICY + 'allowed_channel', 'if not allowed_channel(event):', '    return'])
            text=main.read_text().replace('@filter.event_message_type(filter.EventMessageType.ALL)',
                '@filter.event_message_type(filter.EventMessageType.ALL, priority=150)')
            text=text.replace('await self.sender.send_parse_result(event, parse_res)',
                'await self.sender.send_parse_result(event, parse_res)\n        event.stop_event()')
            main.write_text(text,encoding='utf-8')
        if name == 'astrbot_plugin_anysearch':
            inject_functions(main, lambda n: n.name == 'anysearch_batch_search',
                lambda n: [POLICY + 'owner_private, public_query',
                           'if not owner_private(event) or not public_query(queries):',
                           "    return '当前会话或查询不允许联网。'"])
            inject_functions(main, lambda n: n.name == 'search_command',
                lambda n: [POLICY + 'owner_private, public_query',
                           'if not owner_private(event) or not public_query(query):', '    return'])
        if name == 'astrbot_plugin_qq_tools':
            inject_functions(main,
                lambda n: any(a.arg == 'event' for a in n.args.args) and bool(n.decorator_list),
                lambda n: [POLICY + 'allowed_channel', 'if not allowed_channel(event):', '    return'])
        # FunctionTool implementations are guarded at execution as well as filtered from prompts.
        candidates = list((target / 'tools').glob('*.py')) if (target / 'tools').is_dir() else [target / 'tools.py']
        for path in candidates:
            if not path.exists():continue
            if name == 'astrbot_plugin_anysearch':
                inject_functions(path, lambda n: n.name == 'run' and any(a.arg=='event' for a in n.args.args),
                    lambda n: [POLICY + 'owner_private, public_query',
                               'if not owner_private(event) or not public_query('+('query' if any(a.arg=='query' for a in n.args.args) else 'url')+'):',
                               "    return '当前会话或查询不允许联网。'"])
            inject_functions(path, lambda n: n.name == 'call' and any(a.arg=='context' for a in n.args.args),
                lambda n: [POLICY + 'allowed_tool_call',
                           'if not allowed_tool_call(context.context.event, self.name, kwargs):',
                           "    return '当前会话或参数不允许调用此工具。'"])
        for path in target.rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8-sig'))
        print('PREPARED',name,flush=True)


if __name__ == '__main__':prepare(*sys.argv[1:3])
