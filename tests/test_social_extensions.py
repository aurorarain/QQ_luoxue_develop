import datetime
import importlib
import json
import pathlib
import time
import types
import unittest
from unittest.mock import AsyncMock,patch

from test_boundaries import main,features
from luoxue_social import web_search,image_api,persona

class Extensions(unittest.IsolatedAsyncioTestCase):
    async def test_clock_counts_seconds_not_guessed_hours(self):
        social=main.Social.__new__(main.Social)
        social.state={'previous_clock_group':time.time()-120}
        text=social.clock_context('group')
        self.assertIn('+08:00',text)
        self.assertIn('120',text)

    async def test_semantic_pool_recovers_after_small_category_exhausted(self):
        f=features.Features.__new__(features.Features)
        f.s=types.SimpleNamespace(state={'meme_recent':{'g':['a','b']}},save=lambda:None)
        f.index=[{'sha':x,'category':'开心','scope':'public','file':x+'.gif'} for x in ['a','b']]
        f.library=pathlib.Path('/tmp');f._save_index=lambda:None
        self.assertEqual(f.choose_meme('开心',False,'g').name,'a.gif')
        self.assertIsNone(f.choose_meme('生气',False,'g'))

    async def test_public_search_returns_sources_without_credentials(self):
        f=features.Features.__new__(features.Features)
        f.s=types.SimpleNamespace(state={},save=lambda:None);f.cfg={}
        body=b'<rss><channel><item><title>public example</title><link>https://example.org/topic</link><description>source summary</description></item></channel></rss>'
        with patch.object(features,'fetch',AsyncMock(return_value=body)) as call:
            result=await web_search.search(f,'公开网络热梗')
            self.assertEqual(len(result['items']),1)
            self.assertNotIn('Authorization',str(call.call_args))
            await web_search.search(f,'公开网络热梗')
            self.assertEqual(call.await_count,1)
        self.assertIn('error',await web_search.search(f,'查询验证码'))

    async def test_proactive_group_never_receives_private_material(self):
        captures=[];sent=[];now=time.time()
        async def generate(prompt,system):
            captures.append(prompt+system)
            return json.dumps({'send':True,'text':'这场白米饭辩论，我先申请加一碗。'})
        async def send(target,chain):sent.append(target)
        s=types.SimpleNamespace(state={'private':[{'text':'PRIVATE_CANARY'}],
            'group_observed':[{'time':now-200,'sender':'public','text':'白米饭好吃'}]*3,'group_last_human':now-200},
            save=lambda:None,generate=generate,context=types.SimpleNamespace(send_message=send),add=lambda *a:None)
        f=features.Features.__new__(features.Features);f.s=s;f.group='20001'
        f.reply_chain=lambda text,private,session:[]
        await f.proactive_group(datetime.datetime(2026,10,29,12))
        self.assertEqual(sent,['napcat:GroupMessage:20001'])
        self.assertNotIn('PRIVATE_CANARY',''.join(captures))
        await f.proactive_group(datetime.datetime(2026,10,29,12))
        self.assertEqual(len(sent),1)

    async def test_group_excerpt_has_no_private_source(self):
        prompts=[]
        async def generate(prompt,system):
            prompts.append(prompt);return '{"share":true,"indices":[0,1]}'
        f=features.Features.__new__(features.Features)
        f.s=types.SimpleNamespace(state={'private':[{'text':'SECRET_CANARY'}],
            'group':[{'sender':'洛雪','text':'白米饭第一。'},{'sender':'public','text':'加一碗。'}]},generate=generate)
        f.make_card=AsyncMock(return_value='/tmp/card.png')
        self.assertEqual(await f.group_excerpt('群里又在争米饭了'),['/tmp/card.png'])
        self.assertNotIn('SECRET_CANARY',''.join(prompts))
        self.assertIn('非QQ原始截图',f.make_card.call_args.args[0]['source'])

    async def test_wan26_official_protocol(self):
        result={'output':{'choices':[{'message':{'content':[{'image':'https://example.org/image.png'}]}}]}}
        with patch.object(features,'fetch',AsyncMock(side_effect=[json.dumps(result).encode(),b'PNG'])) as call:
            body=await image_api.generate({'base_url':'https://dashscope.aliyuncs.com','api_key':'TEST_CANARY','model':'wan2.6-t2i'},'鲸鱼娘')
            self.assertEqual(body,b'PNG')
            self.assertIn('multimodal-generation',call.call_args_list[0].args[0])
            self.assertEqual(call.call_args_list[0].kwargs['json_body']['parameters']['size'],'1280*1280')
        with self.assertRaises(ValueError):
            await image_api.generate({'base_url':'https://example.org','api_key':'x','model':'wan2.6-t2i'},'x')

    async def test_wan20_async_protocol_polls_without_resubmission(self):
        responses=[json.dumps({'output':{'task_id':'test-task-123'}}).encode(),
                   json.dumps({'output':{'task_status':'SUCCEEDED','results':[{'url':'https://example.org/a.png'}]}}).encode(),b'PNG']
        with patch.object(features,'fetch',AsyncMock(side_effect=responses)) as call,patch.object(image_api.asyncio,'sleep',AsyncMock()):
            body=await image_api.generate({'base_url':'https://dashscope.aliyuncs.com','api_key':'TEST_CANARY','model':'wanx2.0-t2i-turbo'},'鲸鱼娘')
            self.assertEqual(body,b'PNG')
            self.assertEqual(call.call_args_list[0].kwargs['headers']['X-DashScope-Async'],'enable')
            self.assertIn('/tasks/test-task-123',call.call_args_list[1].args[0])
            self.assertEqual(sum('json_body' in c.kwargs for c in call.call_args_list),1)

    async def test_wan20_rejects_unsupported_square_before_submit(self):
        with patch.object(features,'fetch',AsyncMock()) as call:
            with self.assertRaises(ValueError):
                await image_api.generate({'base_url':'https://dashscope.aliyuncs.com','api_key':'TEST_CANARY',
                    'model':'wanx2.0-t2i-turbo','size':'1280*1280'},'test')
            call.assert_not_awaited()

    async def test_empty_tool_runtime_guard(self):
        try:module=importlib.import_module('astrbot.core.agent.runners.tool_loop_agent_runner')
        except ImportError:self.skipTest('requires AstrBot runtime')
        from luoxue_social.runtime_guard import install_runner_guard
        seen=[]
        async def reset(self,*args,**kwargs):seen.append(kwargs['tool_schema_mode'])
        with patch.object(module.ToolLoopAgentRunner,'reset',reset):
            install_runner_guard();first=module.ToolLoopAgentRunner.reset
            install_runner_guard();self.assertIs(first,module.ToolLoopAgentRunner.reset)
            obj=module.ToolLoopAgentRunner.__new__(module.ToolLoopAgentRunner)
            await obj.reset(request=types.SimpleNamespace(func_tool=None),tool_schema_mode='skills_like')
            self.assertEqual(seen,['full'])

    def test_new_identity_is_nonromantic_and_boss_bound(self):
        self.assertIn('唯一老大',persona.PERSONA)
        self.assertIn('不是女友',persona.PERSONA)
        self.assertIn('白米饭',persona.PERSONA)

    def test_banter_rules_stay_playful_not_bureaucratic(self):
        # 2026-10-30: she answered "我不就是alex吗" with "号对得上，验过了" and treated a
        # joke as a transaction ("那单交易我不认"). Guard the replacement rules.
        for phrase in ['先接住对方的梗','别把玩笑当正事办','不要求对方解释','公事公办腔','第一反应要短']:
            self.assertIn(phrase,persona.PERSONA)
        self.assertIn('玩笑',persona.PUBLIC_PERSONA)

    def test_group_instructions_treat_banter_as_banter(self):
        f=features.Features.__new__(features.Features)
        f.s=types.SimpleNamespace(state={},save=lambda:None)
        f.cfg={};f.owner='10001';f.index=[];f.index_path=pathlib.Path('/not-used')
        f.capabilities=lambda:{'features':{},'plugins':[],'plugin_root':'/not-used'}
        text=f.public_instructions('90001')
        self.assertIn('默认对方在逗你',text)
        self.assertIn('验过了',text)  # named as something not to say
        private=f.private_instructions()
        self.assertIn('别把它当成需要你表态认不认的事',private)
