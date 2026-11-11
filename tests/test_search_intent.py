# All identities, messages, locations and media in this file are synthetic test fixtures.
import unittest

import test_boundaries  # noqa: F401
from luoxue_social import web_search


SHOP_QUESTION = ('这些示例品牌这类在示例商城全有吗，价格会不会虚高，和其他商场比，'
                 '我现在住在上海市，示例商城不算远')


class PublicQuery(unittest.TestCase):
    def test_first_person_clauses_are_dropped(self):
        query = web_search.public_query(SHOP_QUESTION)
        self.assertIn('示例商城', query)
        self.assertIn('价格', query)
        self.assertNotIn('上海市', query)
        self.assertNotIn('我住', query)

    def test_all_personal_message_yields_no_query(self):
        self.assertEqual(web_search.public_query('我住在上海市，我家在几楼'), '')

    def test_query_length_is_bounded(self):
        self.assertLessEqual(len(web_search.public_query('店' * 300)), 40)
