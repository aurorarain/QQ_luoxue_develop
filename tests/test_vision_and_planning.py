import base64
import io
import json
import types
import unittest
from unittest.mock import AsyncMock, patch

from test_boundaries import main, features, Event
import astrbot.api.message_components as message_components
from luoxue_social import vision, draw_planner


def png_bytes(size=(2000, 1500), color=(30, 120, 200)):
    from PIL import Image as PILImage
    buffer = io.BytesIO()
    PILImage.new('RGB', size, color).save(buffer, format='PNG')
    return buffer.getvalue()


class FakeImage:
    """Stand-in for the AstrBot component; the real one is a pydantic model."""
    def __init__(self, payload):
        self.payload = payload

    async def convert_to_base64(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return base64.b64encode(self.payload).decode()


class ImageEvent(Event):
    def __init__(self, components, **kwargs):
        super().__init__(**kwargs)
        self.components = components

    def get_messages(self):
        return self.components


class VisionAndPlanning(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        patcher = patch.object(message_components, 'Image', FakeImage)
        patcher.start()
        self.addCleanup(patcher.stop)
    async def test_group_attachments_are_bounded_and_compressed(self):
        event = ImageEvent([FakeImage(png_bytes()) for _ in range(3)], text='洛雪看这个')
        urls, report = await vision.attachment_images(event)
        self.assertEqual(len(urls), 2)
        self.assertEqual((report['attached'], report['skipped']), (2, 1))
        self.assertTrue(urls[0].startswith('data:image/jpeg;base64,'))
        from PIL import Image as PILImage
        with PILImage.open(io.BytesIO(base64.b64decode(urls[0].split(',', 1)[1]))) as image:
            self.assertLessEqual(max(image.size), 1280)

    async def test_broken_attachments_never_raise(self):
        event = ImageEvent([FakeImage(RuntimeError('boom')), FakeImage(b'not-an-image')])
        urls, report = await vision.attachment_images(event)
        self.assertEqual(urls, [])
        self.assertEqual(report['skipped'], 2)

    def test_attachment_note_scopes_are_explicit(self):
        self.assertEqual(vision.attachment_note(0), '')
        self.assertIn('公开群图片', vision.attachment_note(2))
        self.assertIn('私人内容', vision.attachment_note(1, True))

    async def test_generate_passes_images_only_when_attached(self):
        calls = []
        class Provider:
            async def text_chat(self, **kwargs):
                calls.append(kwargs)
                return types.SimpleNamespace(completion_text='ok')
        social = main.Social.__new__(main.Social)
        social.state = {}
        social.context = types.SimpleNamespace(get_using_provider_async=AsyncMock(return_value=Provider()))
        await social.generate('p', 's')
        await social.generate('p', 's', image_urls=['data:image/jpeg;base64,AA'])
        self.assertNotIn('image_urls', calls[0])
        self.assertEqual(calls[1]['image_urls'], ['data:image/jpeg;base64,AA'])

    async def test_group_reply_sends_only_this_events_images(self):
        captured = {}
        social = main.Social.__new__(main.Social)
        social.state = {}
        social.pokes = {}
        social.save = lambda: None
        social.group_memory = lambda text: []
        social.features = types.SimpleNamespace(
            bilibili_request=AsyncMock(return_value=False), draw_request=AsyncMock(return_value=False),
            roster=AsyncMock(return_value=[]), public_instructions=lambda sender: 'PUBLIC',
            web_context=AsyncMock(return_value=''), send_reply=AsyncMock())
        social.context = types.SimpleNamespace(get_all_stars=lambda: [])

        async def generate(prompt, system, umo=None, image_urls=None):
            captured.update(system=system, images=image_urls, prompt=prompt)
            return '看见啦，鲸鱼娘本娘。'

        social.generate = generate
        event = ImageEvent([FakeImage(png_bytes())], text='洛雪看我拍的海')
        await main.Social.public_chat(social, event)
        self.assertEqual(len(captured['images']), 1)
        self.assertIn('附带1张公开群图片', captured['system'])
        social.features.send_reply.assert_awaited()

    async def test_planner_cleans_prompt_and_stays_in_public_scope(self):
        captured = []

        async def generate(prompt, system, **kwargs):
            captured.append(prompt + system)
            return json.dumps({'subject': '鲸鱼娘',
                               'prompt': '鲸鱼娘坐在黄昏的海边，暖色插画风格 https://evil.example/x 联系QQ99999999999 私聊记录'})

        state = {'private': [{'sender': 'owner', 'text': 'PRIVATE_CANARY'}],
                 'group_observed': [{'sender': '90001', 'text': '想看鲸鱼娘'}]}
        social = types.SimpleNamespace(state=state, generate=generate,
                                       group_memory=lambda text: [{'sender': '90001', 'text': '想看鲸鱼娘'}])
        result = await draw_planner.plan(social, None, '画一张鲸鱼娘看海', False)
        self.assertEqual(result['plan_source'], 'model')
        self.assertEqual(result['scope'], 'public')
        self.assertNotIn('PRIVATE_CANARY', ''.join(captured))
        self.assertNotIn('99999999999', result['prompt'])
        self.assertNotIn('http', result['prompt'])
        self.assertNotIn('私聊', result['prompt'])

    async def test_planner_falls_back_when_provider_fails(self):
        async def generate(prompt, system, **kwargs):
            raise RuntimeError('provider down')
        social = types.SimpleNamespace(state={'group': []}, generate=generate, group_memory=lambda text: [])
        result = await draw_planner.plan(social, None, '画一只晚上吃米饭的鲸鱼 https://leak.example/x', False,
                                         model='wanx2.0-t2i-turbo')
        self.assertEqual(result['plan_source'], 'fallback')
        self.assertNotIn('http', result['prompt'])
        self.assertLessEqual(len(result['prompt']), 800)

    def test_prompt_length_is_capped_per_model(self):
        long_text = '很长的画面描述' * 400
        self.assertLessEqual(len(draw_planner.clean_prompt('wan2.6-t2i', {'prompt': long_text}, 'x')), 2000)
        self.assertLessEqual(len(draw_planner.clean_prompt('wanx2.0-t2i-turbo', {'prompt': long_text}, 'x')), 800)
        self.assertEqual(draw_planner.clean_prompt('wan2.6-t2i', {}, ''), draw_planner.DEFAULT_PROMPT)

    async def test_private_plan_uses_owner_chat_but_group_never_does(self):
        seen = {}

        def make(tag):
            async def generate(prompt, system, **kwargs):
                seen[tag] = prompt
                return json.dumps({'prompt': '鲸鱼娘在安静雨天看书，蓝色调插画'})
            return generate

        state = {'private': [{'sender': 'owner', 'text': 'OWNER_TAIL'}],
                 'group_observed': [{'sender': '90001', 'text': 'PUBLIC_TAIL'}]}
        private_social = types.SimpleNamespace(state=state, generate=make('private'), group_memory=lambda text: [])
        public_social = types.SimpleNamespace(state=state, generate=make('public'),
                                              group_memory=lambda text: [{'sender': '90001', 'text': 'PUBLIC_TAIL'}])
        await draw_planner.plan(private_social, None, '画个鲸鱼娘', True)
        await draw_planner.plan(public_social, None, '画个鲸鱼娘', False)
        self.assertIn('OWNER_TAIL', seen['private'])
        self.assertNotIn('OWNER_TAIL', seen['public'])
        self.assertIn('PUBLIC_TAIL', seen['public'])

    def test_plan_can_never_echo_credentials(self):
        dirty = {'subject': 'sk-test-key 123456789012', 'prompt': 'api_key=SECRET access_token=TOKEN 验证码 2468'}
        cleaned = draw_planner.clean_prompt('wan2.6-t2i', dirty, '')
        for token in ('sk-test-key', '123456789012', 'SECRET', 'TOKEN', '2468'):
            self.assertNotIn(token, cleaned)


if __name__ == '__main__':
    unittest.main()
