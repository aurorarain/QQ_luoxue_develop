"""Synthetic conversations test model-owned search choices, never keyword triggers."""
import datetime as dt
import json
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import test_boundaries
from luoxue_social import web_search


class AutonomousSearch(unittest.IsolatedAsyncioTestCase):
    def feature(self, action='respond', query='', **state):
        generate=AsyncMock(return_value=json.dumps({'action':action,'query':query,'reason':'合成测试决定'}))
        return SimpleNamespace(cfg={'web_search':{'tavily_api_key':'SYNTHETIC_TOKEN'}},
            s=SimpleNamespace(state=state,save=lambda:None,generate=generate))

    async def test_message_without_trigger_words_can_lead_to_search(self):
        f=self.feature('search','公开花卉资料')
        with patch.object(web_search,'search',AsyncMock(return_value={'items':[]})) as call:
            await web_search.automatic_context(f,'窗边的花忽然让我好奇起来','group','speaker-a','group-session')
        call.assert_awaited_once_with(f,'公开花卉资料')
        self.assertEqual(f.s.generate.call_args.args[2],'group-session')
        self.assertEqual(f.s.state['web_decision_log'][-1]['source'],'model')

    async def test_search_word_does_not_force_search(self):
        f=self.feature('respond')
        with patch.object(web_search,'search',AsyncMock()) as call:
            note=await web_search.automatic_context(f,'会搜索也不用每句话都查吧','group','speaker-a')
        f.s.generate.assert_awaited_once()
        call.assert_not_awaited()
        self.assertIn('自主决定先不联网',note)

    async def test_followup_is_resolved_by_model_from_conversation(self):
        f=self.feature('search','"蓝雨糖" 含义',group=[
            {'text':'蓝雨糖是个什么说法','sender':'speaker-a','time':time.time()-2}])
        with patch.object(web_search,'search',AsyncMock(return_value={'items':[]})) as call:
            await web_search.automatic_context(f,'要不你看看呢','group','speaker-a')
        self.assertIn('蓝雨糖',f.s.generate.call_args.args[0])
        call.assert_awaited_once_with(f,'"蓝雨糖" 含义')

    async def test_private_history_never_reaches_group_decision(self):
        now=time.time()
        f=self.feature(group=[{'text':'PUBLIC_CANARY','sender':'speaker-a','time':now}],
            private=[{'text':'PRIVATE_CANARY','sender':'speaker-a','time':now}])
        await web_search.automatic_context(f,'接着刚才的话','group','speaker-a')
        prompt=f.s.generate.call_args.args[0]
        self.assertIn('PUBLIC_CANARY',prompt);self.assertNotIn('PRIVATE_CANARY',prompt)

    async def test_private_decision_only_receives_private_channel_history(self):
        now=time.time()
        f=self.feature(group=[{'text':'GROUP_CANARY','sender':'other','time':now}],
            private=[{'text':'OWNER_CANARY','sender':'speaker-a','time':now}])
        await web_search.automatic_context(f,'接着聊','private','speaker-a')
        prompt=f.s.generate.call_args.args[0]
        self.assertIn('OWNER_CANARY',prompt);self.assertNotIn('GROUP_CANARY',prompt)

    async def test_planner_knows_both_remaining_limits(self):
        now=dt.datetime.now(ZoneInfo('Asia/Shanghai'))
        f=self.feature(web_usage_v2={'day':now.strftime('%Y-%m-%d'),'month':now.strftime('%Y-%m'),
                                   'count':3,'credits':12})
        await web_search.automatic_context(f,'聊聊今天','group','speaker-a')
        payload=json.loads(f.s.generate.call_args.args[0]);budget=payload['search_budget']
        self.assertEqual(budget['daily_remaining'],22)
        self.assertEqual(budget['monthly_remaining'],888)

    async def test_exhausted_budget_blocks_network(self):
        now=dt.datetime.now(ZoneInfo('Asia/Shanghai'))
        f=self.feature('search','公开资料',web_usage_v2={'day':now.strftime('%Y-%m-%d'),'count':25},
            web_page_usage={'day':now.strftime('%Y-%m-%d'),'count':20})
        with patch.object(web_search,'search',AsyncMock()) as call:
            await web_search.automatic_context(f,'想查点资料','group','speaker-a')
        call.assert_not_awaited();f.s.generate.assert_not_awaited()

    async def test_invalid_decision_never_falls_back_to_keywords(self):
        f=self.feature();f.s.generate.return_value='not JSON'
        with patch.object(web_search,'search',AsyncMock()) as call:
            note=await web_search.automatic_context(f,'搜索最新新闻','group','speaker-a')
        call.assert_not_awaited();self.assertIn('没有实际检索',note)

    async def test_clarify_choice_does_not_search(self):
        f=self.feature('clarify')
        with patch.object(web_search,'search',AsyncMock()) as call:
            note=await web_search.automatic_context(f,'就是那个呀','group','speaker-a')
        call.assert_not_awaited();self.assertIn('先问清',note)

    async def test_personal_clauses_and_credentials_are_redacted_before_plan(self):
        f=self.feature()
        await web_search.automatic_context(f,'我住在合成地址，看看花卉，tvly-SYNTHETIC1234','group','speaker-a')
        prompt=f.s.generate.call_args.args[0]
        self.assertNotIn('合成地址',prompt)
        self.assertNotIn('tvly-SYNTHETIC1234',prompt)
        self.assertIn('花卉',prompt)

    def test_runtime_has_no_keyword_trigger_router(self):
        self.assertFalse(hasattr(web_search,'search_intent'))
        self.assertFalse(hasattr(web_search,'EXPLICIT'))

    def test_quoted_terms_exclude_generic_tutorials(self):
        rows=[{'title':'搜索教程','content':'搜一搜含义与使用方法','url':'https://example.org/help'},
              {'title':'蓝雨糖','content':'合成测试术语蓝雨糖','url':'https://example.org/term'}]
        items=web_search.normalized_results({'results':rows},'tavily','"蓝雨糖" 含义 出处')
        self.assertEqual([item['url'] for item in items],['https://example.org/term'])
