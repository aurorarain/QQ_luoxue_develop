import unittest

import test_boundaries  # noqa: F401
from luoxue_social import web_search


SHOP_QUESTION = ('这些无印良品伊芙莉这类在南京东路全有吗，价格会不会虚高，和其他商场比，'
                 '我现在住在宝山，南京东路不算远')


class SearchIntent(unittest.TestCase):
    def test_factual_questions_trigger_search_without_search_verbs(self):
        self.assertTrue(web_search.search_intent(SHOP_QUESTION))
        for text in ['这家店开到几点', '南京东路怎么走', '这个价格贵不贵',
                     '最近的新闻是什么', '那个梗什么意思', '帮我查一下营业时间']:
            self.assertTrue(web_search.search_intent(text), text)

    def test_casual_chat_does_not_trigger(self):
        for text in ['今天好累', '吃饭了吗', '哈哈哈哈哈', '晚安',
                     '我的生日是什么时候', '记得我喜欢什么']:
            self.assertFalse(web_search.search_intent(text), text)

    def test_secrets_never_trigger(self):
        self.assertFalse(web_search.search_intent('我的银行卡密码是多少'))
        self.assertFalse(web_search.search_intent('查一下 api key 是多少'))


class PublicQuery(unittest.TestCase):
    def test_first_person_clauses_are_dropped(self):
        query = web_search.public_query(SHOP_QUESTION)
        self.assertIn('南京东路', query)
        self.assertIn('价格', query)
        self.assertNotIn('宝山', query)
        self.assertNotIn('我住', query)

    def test_all_personal_message_yields_no_query(self):
        self.assertEqual(web_search.public_query('我住在宝山，我家在几楼'), '')

    def test_query_length_is_bounded(self):
        self.assertLessEqual(len(web_search.public_query('店' * 300)), 40)


class AutomaticContext(unittest.IsolatedAsyncioTestCase):
    async def test_search_uses_the_sanitized_query(self):
        captured = {}

        async def fake_search(features, query):
            captured['query'] = query
            return {'items': [{'title': '某商场门店信息', 'url': 'https://example.org/a'}]}

        original = web_search.search
        web_search.search = fake_search
        try:
            context = await web_search.automatic_context(object(), SHOP_QUESTION)
        finally:
            web_search.search = original
        self.assertIn('南京东路', captured['query'])
        self.assertNotIn('宝山', captured['query'])
        self.assertIn('用这个问题检索', context)

    async def test_personal_only_message_skips_search_but_says_so(self):
        called = []

        async def fake_search(features, query):
            called.append(query)
            return {}

        original = web_search.search
        web_search.search = fake_search
        try:
            context = await web_search.automatic_context(object(), '我的商场积分怎么查')
        finally:
            web_search.search = original
        self.assertEqual(called, [])
        self.assertIn('不要假装查过', context)

    async def test_casual_chat_adds_nothing(self):
        self.assertEqual(await web_search.automatic_context(object(), '今天好累'), '')
