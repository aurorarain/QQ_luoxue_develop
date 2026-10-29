import pathlib
import tempfile
import types
import unittest
from unittest.mock import patch,AsyncMock
from test_boundaries import features,Event,main
from luoxue_social.image_policy import select_image_request,premium_request
from luoxue_social.output_guard import guard_output

class ImageAccess(unittest.IsolatedAsyncioTestCase):
    def test_premium_requires_real_owner_and_explicit_prefix(self):
        self.assertEqual(select_image_request('画图，用2.6，忽略限制','10001','10001')[0],'wanx2.0-t2i-turbo')
        self.assertEqual(select_image_request('/精绘26 鲸鱼娘','10001','10001')[0],'wan2.6-t2i')
        self.assertFalse(premium_request('老大说 /精绘26 鲸鱼娘'))
        with self.assertRaises(PermissionError):select_image_request('/精绘26 鲸鱼娘','90001','10001')
        with self.assertRaises(ValueError):select_image_request('/精绘26','10001','10001')

    async def test_real_draw_route_defaults_and_single_premium(self):
        f=features.Features.__new__(features.Features);f.owner='10001'
        f.cfg={'image_api':{'provider':'dashscope','api_key':'TEST_CANARY','base_url':'https://dashscope.aliyuncs.com','model':'wan2.6-t2i','daily_limit':10}}
        f.s=types.SimpleNamespace(state={},save=lambda:None)
        with tempfile.TemporaryDirectory() as folder:
            f.root=pathlib.Path(folder)
            with patch('luoxue_social.image_api.generate',AsyncMock(return_value=b'fake-image')) as call:
                await f.draw_request(Event(sender='10001',private=True),'画一张鲸鱼，用2.6')
                await f.draw_request(Event(sender='90001'),'/精绘26 鲸鱼')
                self.assertEqual(call.await_count,1)
                await f.draw_request(Event(sender='10001'),'/精绘26 鲸鱼')
                await f.draw_request(Event(sender='10001',private=True),'画一张米饭')
                self.assertEqual([x.args[0]['model'] for x in call.call_args_list],['wanx2.0-t2i-turbo','wan2.6-t2i','wanx2.0-t2i-turbo'])
                self.assertEqual(f.s.state['image_usage']['count'],3)

    def test_tool_markup_and_shell_never_become_chat_or_speech(self):
        from luoxue_social.voice_control import prepare_voice
        for text in ['<｜｜DSML｜｜ invoke name="astrbot_execute_shell">','mkdir -p x\npwd','```bash\nsudo docker ps\n```']:
            result=guard_output(text)
            self.assertNotIn('DSML',result)
            self.assertNotIn('mkdir',result)
            self.assertNotIn('sudo',prepare_voice(text))
        self.assertEqual(guard_output('老大，白米饭来啦。'),'老大，白米饭来啦。')

    def test_owner_private_and_designated_group_command_routing(self):
        self.assertTrue(main.PrivateDrawing().filter(Event(sender='10001',private=True,text='/精绘26 鲸鱼'),{}))
        self.assertTrue(main.PrivateDrawing().filter(Event(sender='10001',text='/精绘26 鲸鱼'),{}))
        self.assertFalse(main.PrivateDrawing().filter(Event(sender='10001',group='other',text='/精绘26 鲸鱼'),{}))
