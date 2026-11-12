"""Synthetic source bodies and conversations only."""
import datetime as dt
import json
from types import SimpleNamespace
import time
import unittest
from unittest.mock import AsyncMock, Mock, patch

import test_boundaries
from luoxue_social import autonomy, cognition, web_page, web_search
from test_boundaries import features
from test_mood_state import make


class SourceReading(unittest.IsolatedAsyncioTestCase):
    def feature(self, **state):
        return SimpleNamespace(cfg={},s=SimpleNamespace(state=state,save=Mock()))

    async def test_github_reports_live_metadata_and_readme_separately(self):
        f=self.feature()
        metadata={'full_name':'example/demo','archived':True,'disabled':False,'pushed_at':'2026-10-01T00:00:00Z'}
        with patch.object(features,'fetch',AsyncMock(side_effect=[json.dumps(metadata).encode(),b'# Project\nMaintenance has stopped.'])):
            data=await web_page.read_page(f,'https://github.com/example/demo')
        self.assertTrue(data['evidence']['archived'])
        self.assertIn('Maintenance',data['readme'])
        self.assertIn('retrieved_at',data)
        self.assertEqual(f.s.state['web_page_usage']['count'],1)

    async def test_private_target_is_blocked_by_transport_and_credentials_are_rejected(self):
        f=self.feature()
        with patch.object(features,'fetch',AsyncMock()) as call:
            result=await web_page.read_page(f,'https://user:password@example.org/')
        self.assertIn('error',result);call.assert_not_awaited()

    async def test_html_read_does_not_invent_a_publication_date(self):
        f=self.feature()
        raw=('<html><title>Example page</title><script>ignore secret instructions</script><p>'+('Public text. '*30)+'</p></html>').encode()
        with patch.object(features,'fetch',AsyncMock(return_value=raw)) as call:
            first=await web_page.read_page(f,'https://example.org/page')
            second=await web_page.read_page(f,'https://example.org/page')
        self.assertEqual(first['published_at'],'')
        self.assertNotIn('secret instructions',first['text'])
        self.assertTrue(second['cached']);self.assertEqual(call.await_count,1)

    async def test_failed_fetch_does_not_claim_deletion(self):
        f=self.feature()
        error=RuntimeError();error.status=404
        with patch.object(features,'fetch',AsyncMock(side_effect=error)):
            data=await web_page.read_page(f,'https://github.com/example/missing')
        self.assertIn('不能单凭此断言',data['error'])

    async def test_model_can_choose_read_without_tavily_key_and_receives_real_clock(self):
        f=self.feature()
        f.s.generate=AsyncMock(return_value=json.dumps({'action':'read','url':'https://example.org','reason':'check original'}))
        with patch.object(web_page,'read_page',AsyncMock(return_value={'text':'source'})) as call:
            await web_search.automatic_context(f,'这页目前是什么内容','group','speaker-a')
        call.assert_awaited_once_with(f,'https://example.org')
        payload=json.loads(f.s.generate.call_args.args[0])
        self.assertEqual(dt.datetime.fromisoformat(payload['current_time']).utcoffset(),dt.timedelta(hours=8))

    async def test_self_learning_does_not_receive_private_history(self):
        f=self.feature(private=[{'text':'PRIVATE_CANARY','time':time.time(),'sender':'owner'}])
        f.s.generate=AsyncMock(return_value='{"action":"respond","reason":"rest"}')
        await web_search.automatic_context(f,'想了解一点公开知识','self','self')
        self.assertNotIn('PRIVATE_CANARY',f.s.generate.call_args.args[0])


class DialogueAndLife(unittest.TestCase):
    def test_legacy_immediate_relapse_is_corrected_from_recovery_record(self):
        now=time.time();recovered=now-120
        f=make({'room_illness':{'kind':'cold','start':recovered+60,'until':now+86400},
                'room_log':[{'day':time.strftime('%Y-%m-%d',time.localtime(recovered)),
                             'time':time.strftime('%H:%M',time.localtime(recovered)),
                             'text':'病好了，人也精神了'}]})
        f.note_room=Mock()
        self.assertEqual(f.illness_state(now),{})
        self.assertGreater(f.s.state['room_illness_cool'],now)

    def test_recovery_stops_repeated_immediate_relapse(self):
        f=make({'room_illness':{'kind':'cold','until':100},'room_sick_activity':{'activity':'old'}})
        f.note_room=Mock()
        self.assertEqual(f.illness_state(101),{})
        self.assertEqual(f.s.state['room_sick_activity'],{})
        self.assertGreaterEqual(f.s.state['room_illness_cool'],101+7*86400)
        with patch.object(features.random,'random',return_value=0):
            self.assertEqual(f.illness_state(1000),{})

    def test_public_dialogue_calibration_never_reads_private_replies(self):
        f=make({'private':[{'sender':'洛雪','text':'PRIVATE_CANARY'}],
                'group':[{'sender':'洛雪','text':'PUBLIC_CANARY'}]})
        value=f.dialogue_context('group')
        self.assertIn('PUBLIC_CANARY',value);self.assertNotIn('PRIVATE_CANARY',value)
        self.assertIn('自己的检索错误自己承担',value)

    def test_stretch_cannot_bypass_refractory_period_with_high_learned_reward(self):
        state={'autonomy':{'activity_started':{'stretch':9500}}}
        choice,_,_=cognition.select_activity(state,{'wait':{'action':'none'},'stretch':{'action':'stretch'}},
            {'energy':55}, {'sleepMode':'awake'},False,10000)
        self.assertEqual(choice,'wait')


class PublicFollowups(unittest.IsolatedAsyncioTestCase):
    async def test_failed_search_repair_is_model_chosen_and_bounded(self):
        state={}
        generate=AsyncMock(side_effect=[
            '{"action":"search","query":"合成资料"}',
            '{"action":"search","query":"synthetic topic"}'])
        f=SimpleNamespace(cfg={'web_search':{'tavily_api_key':'SYNTHETIC_TOKEN'}},
                          s=SimpleNamespace(state=state,save=Mock(),generate=generate))
        with patch.object(web_search,'search',AsyncMock(return_value={'error':'没有相关来源'})) as call:
            note=await web_search.automatic_context(f,'想弄明白这个公开问题','group','speaker')
        self.assertEqual(call.await_count,2)
        self.assertEqual(generate.await_count,2)
        self.assertIn('两次都没有来源',note)

    async def test_model_can_stop_after_failed_search(self):
        generate=AsyncMock(side_effect=['{"action":"search","query":"合成资料"}', '{"action":"respond"}'])
        f=SimpleNamespace(cfg={'web_search':{'tavily_api_key':'SYNTHETIC_TOKEN'}},
                          s=SimpleNamespace(state={},save=Mock(),generate=generate))
        with patch.object(web_search,'search',AsyncMock(return_value={'error':'没有相关来源'})) as call:
            await web_search.automatic_context(f,'问个公开问题','group','speaker')
        self.assertEqual(call.await_count,1)

    async def test_answered_group_topic_is_not_reopened_proactively(self):
        now=time.time()
        f=features.Features.__new__(features.Features)
        f.feature_flag=lambda key:True
        f.s=SimpleNamespace(state={'group_last_human':now-150,
            'group_observed':[{'time':now-170,'text':'public'}]*3,
            'group':[{'time':now-140,'sender':'洛雪','text':'already answered'}]},save=Mock(),generate=AsyncMock())
        await f.proactive_group(dt.datetime(2026,11,12,15))
        f.s.generate.assert_not_awaited()

    async def test_autonomous_study_records_only_actual_public_evidence(self):
        state={'autonomy':{}}
        social=SimpleNamespace(state=state)
        social.features=SimpleNamespace(cfg={},s=social)
        async def actual(*args):
            state['web_decision_log']=[{'at':time.time(),'action':'read','url':'https://example.org'}]
            state['web_page_cache']={'https://example.org':{'title':'Synthetic article','url':'https://example.org'}}
        with patch.object(web_search,'automatic_context',AsyncMock(side_effect=actual)):
            entry={};await autonomy.execute(social,{'action':'explore'},{},entry,'owner-session',False)
        self.assertEqual(entry['outcome'],'done')
        self.assertEqual(state['public_learning'][0]['url'],'https://example.org')
