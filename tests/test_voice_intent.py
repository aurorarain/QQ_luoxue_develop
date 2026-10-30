import unittest
from test_boundaries import voice
from luoxue_social.voice_control import wants_voice_reply, prepare_voice


class VoiceIntent(unittest.TestCase):
    def test_real_requests_are_detected(self):
        # The two phrasings that were silently ignored on 2026-10-30:
        self.assertTrue(wants_voice_reply('用语音喊我句老大'))
        self.assertTrue(wants_voice_reply('用语音撒娇撒娇'))
        for text in ['发个语音', '来段语音', '你能发语音吗', '说句话给我听', '用语音说句晚安',
                     '语音条发我', '语音回我一句', '你念给我听', '给我说句话']:
            self.assertTrue(wants_voice_reply(text), text)

    def test_refusals_and_plain_mentions_are_not_requests(self):
        for text in ['别用语音', '不想听语音', '不要发语音', '关闭语音功能', '/说话 测试内容',
                     '语音功能坏了吗', '', '   ', '今天吃的白米饭']:
            self.assertFalse(wants_voice_reply(text), text)

    def test_voice_text_is_cleaned_before_synthesis(self):
        cleaned = prepare_voice('晚安[表情:晚安](｡•̀ᴗ-)✧')
        self.assertTrue(cleaned.startswith('[calm]'))
        self.assertNotIn('表情:', cleaned)
        self.assertNotIn('•', cleaned)
        self.assertNotIn('mkdir', prepare_voice('```bash\nmkdir -p x\n```'))
