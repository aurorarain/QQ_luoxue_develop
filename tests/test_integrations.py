import asyncio
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins'))
from luoxue_social import integration_policy as policy


class IntegrationBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'settings.json'
        self.path.write_text(json.dumps({'owner_qq':'owner','group_qq':'group'}))
        self.env=patch.dict(os.environ,{'LUOXUE_SETTINGS':str(self.path)});self.env.start()

    def tearDown(self):self.env.stop();self.temp.cleanup()

    def event(self,sender='owner',private=True,group='group',text='你好'):
        return SimpleNamespace(is_private_chat=lambda:private,get_sender_id=lambda:sender,
            get_group_id=lambda:group,get_message_str=lambda:text)

    def test_only_owner_private_can_change_profile_or_run_tools(self):
        for event in [self.event(sender='other'),self.event(private=False),self.event(sender='other',private=False)]:
            self.assertFalse(policy.owner_private(event))
            self.assertFalse(policy.allowed_tool_call(event,'change_my_signature',{}))
        self.assertTrue(policy.owner_private(self.event()))

    def test_parser_never_enters_other_private_or_other_group(self):
        self.assertTrue(policy.allowed_channel(self.event(private=False,sender='member')))
        self.assertFalse(policy.allowed_channel(self.event(private=False,group='another')))
        self.assertFalse(policy.allowed_channel(self.event(sender='other')))

    def test_private_poke_never_targets_other_friends(self):
        self.assertFalse(policy.allowed_tool_call(self.event(),'qts_poke_user',{'qq_id':'other'}))
        self.assertTrue(policy.allowed_tool_call(self.event(),'qts_poke_user',{'qq_id':'owner'}))

    def test_message_delete_needs_actual_user_intent(self):
        self.assertFalse(policy.allowed_tool_call(self.event(),'qts_delete_message',{}))
        self.assertTrue(policy.allowed_tool_call(self.event(text='撤回刚才那条'),'qts_delete_message',{}))

    def test_secret_queries_rejected_before_external_call(self):
        self.assertFalse(policy.public_query('帮我搜索 api key sk-secret'))
        self.assertFalse(policy.public_query('查一下我的验证码'))
        self.assertTrue(policy.public_query('AstrBot 官方文档'))

    def test_missing_settings_fails_closed(self):
        self.path.unlink()
        self.assertFalse(policy.owner_private(self.event()))
        self.assertFalse(policy.allowed_channel(self.event(private=False)))


class SearchIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_automatic_group_search_uses_plugin_without_private_history(self):
        web=importlib.import_module('luoxue_social.web_search')
        calls=[]
        async def search(query,max_results):calls.append(query);return '公开搜索来源 https://example.com/'
        instance=SimpleNamespace(client=SimpleNamespace(search=search))
        meta=SimpleNamespace(name='astrbot_plugin_anysearch',activated=True,star_cls=instance)
        social=SimpleNamespace(state={},save=lambda:None,context=SimpleNamespace(get_all_stars=lambda:[meta]))
        feature=SimpleNamespace(s=social,cfg={})
        result=await web.search(feature,'AstrBot 最新版本')
        self.assertEqual(result['provider'],'AnySearch')
        self.assertEqual(calls,['AstrBot 最新版本'])
        cached=await web.search(feature,'AstrBot 最新版本')
        self.assertEqual(cached,result);self.assertEqual(len(calls),1)


if __name__=='__main__':unittest.main()
