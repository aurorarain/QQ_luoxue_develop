"""Read-only staged import and denied-call checks. Does not contact QQ or send messages."""
import asyncio
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace

root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root),str(root/'plugins')]
from luoxue_social import integration_policy as policy
sys.modules['data.plugins.luoxue_social.integration_policy']=policy


async def main():
    event=SimpleNamespace(is_private_chat=lambda:True,get_sender_id=lambda:'not-owner',get_group_id=lambda:'other',get_message_str=lambda:'test')
    profile=importlib.import_module('astrbot_plugin_qqprofile_ex.main')
    assert await profile.QQProfileExPlugin.auto_set_signature(None,event,'test') is None
    relationship=importlib.import_module('astrbot_plugin_relationship.main')
    assert await relationship.RelationshipPlugin.on_llm_request(None,event,None) is None
    parser=importlib.import_module('astrbot_plugin_parser.main')
    assert await parser.ParserPlugin.on_message(None,event) is None
    assert '仅主人' in await parser.ParserPlugin.llm_parse_media_url(None,event,'https://example.com')
    search=importlib.import_module('astrbot_plugin_anysearch.tools')
    assert '不允许' in await search.AnySearchSearchTool().run(event,'public query')
    assert '不允许' in await search.AnySearchExtractTool().run(event,'https://example.com')
    tool=importlib.import_module('astrbot_plugin_qq_tools.tools.get_user_info').GetUserInfoTool()
    context=SimpleNamespace(context=SimpleNamespace(event=event))
    assert '不允许' in await tool.call(context,user_id='any')
    print('UPSTREAM_DENIED_CALLS_OK 7; no provider requests or QQ writes')


if __name__=='__main__':asyncio.run(main())
