import unittest

from test_boundaries import main
from luoxue_social import growth


def social():
    instance = main.Social.__new__(main.Social)
    instance.state = {}
    instance.save = lambda: None
    return instance


HOUR = 3600


class GrowthFlow(unittest.IsolatedAsyncioTestCase):
    def test_three_independent_evidence_then_cooldown(self):
        s = social()
        now = 1000000
        for index in range(2):
            result = growth.observe(s, '开始偏好安静的音乐', '第%d次提到睡前想听纯音乐' % index, now=now + index * 7 * HOUR)
            self.assertTrue(result['ok'], result)
            self.assertLess(result['evidence'], 3)
        third = growth.observe(s, '开始偏好安静的音乐', '第三次主动说想听安静的人声', now=now + 14 * HOUR)
        self.assertTrue(third['ok'])
        self.assertEqual(third['status'], 'ready')
        # Cooldown must block immediate ratification.
        blocked = growth.ratify(s, third['id'], now=now + 15 * HOUR)
        self.assertFalse(blocked['ok'])
        self.assertEqual(blocked['reason'], 'cooldown')
        promoted = growth.ratify(s, third['id'], now=now + 30 * HOUR)
        self.assertTrue(promoted['ok'])
        self.assertIn('开始偏好安静的音乐', growth.active_traits(s))
        self.assertIn('开始偏好安静的音乐', growth.context(s))

    def test_duplicate_and_too_soon_are_rejected(self):
        s = social()
        now = 2000000
        self.assertTrue(growth.observe(s, '爱吃白米饭', '他说我爱吃白米饭', now=now)['ok'])
        self.assertEqual(growth.observe(s, '爱吃白米饭', '他说我爱吃白米饭', now=now + 7 * HOUR)['reason'], 'duplicate')
        self.assertEqual(growth.observe(s, '爱吃白米饭', '别的一句依据', now=now + HOUR)['reason'], 'too_soon')

    def test_revoke_and_reject_keep_audit_trail(self):
        s = social()
        now = 3000000
        for index in range(3):
            result = growth.observe(s, '说话开始带海风比喻', '依据%d' % index, now=now + index * 7 * HOUR)
        self.assertTrue(growth.ratify(s, result['id'], now=now + 40 * HOUR)['ok'])
        self.assertTrue(growth.revoke(s, result['id'], now=now + 50 * HOUR)['ok'])
        self.assertNotIn('说话开始带海风比喻', growth.active_traits(s))
        record = growth.store(s)['ratified'][0]
        self.assertFalse(record['active'])
        self.assertTrue(record['revoked_at'])
        spare = growth.observe(s, '开始喜欢雨天', '他说下雨天我话多', now=now)
        self.assertTrue(growth.reject(s, spare['id'])['ok'])
        self.assertEqual(growth.summary(s)['collecting'], [])

    def test_evidence_is_sanitized(self):
        s = social()
        result = growth.observe(s, '偏好夜间聊天', '电话13800138000 和 https://example.org/x 链接', now=1000)
        self.assertTrue(result['ok'])
        text = growth.store(s)['candidates'][0]['evidence'][0]['text']
        self.assertNotIn('13800138000', text)
        self.assertNotIn('http', text)

    async def test_group_and_other_private_cannot_observe(self):
        instance = social()
        event = type('E', (), {'is_private_chat': lambda self: False,
                               'get_sender_id': lambda self: '90001'})()
        refused = await main.Social.observe_trait_tool(instance, event, '偏好', '依据')
        self.assertIn('只有Alex私聊', refused)
        stranger = type('E', (), {'is_private_chat': lambda self: True,
                                  'get_sender_id': lambda self: '90001'})()
        self.assertIn('只有Alex私聊', await main.Social.observe_trait_tool(instance, stranger, '偏好', '依据'))
        status = await main.Social.growth_status_tool(instance, stranger)
        self.assertIn('只有Alex私聊', status)

    def test_candidate_cap_and_summary_shape(self):
        s = social()
        for index in range(45):
            growth.observe(s, '特征%d' % index, '依据%d' % index, now=1000 + index * 7 * HOUR)
        self.assertLessEqual(len(growth.store(s)['candidates']), growth.MAX_CANDIDATES)
        summary = growth.summary(s)
        for key in ('ready', 'collecting', 'ratified', 'rules'):
            self.assertIn(key, summary)
