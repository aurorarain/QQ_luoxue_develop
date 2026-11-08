# All identities, messages, locations and media in this file are synthetic test fixtures.
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'room_api', Path(__file__).resolve().parents[1] / 'deploy' / 'room_api.py')
room_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(room_api)


class BrainProjection(unittest.TestCase):
    def test_real_state_shape_projects_stable_ids_and_attempt_outcomes(self):
        state = {
            'persona_nodes': [{'id': 'sample', 'text': '喜欢安静', 'tags': ['日常']}],
            'growth': {'ratified': [{'id': 'habit', 'active': True, 'trait': '记得先整理书桌'}]},
            'room_emotions': {'喜': 0, '怒': 30},
            'room_desires': {'听': 23},
            'interests': {'示例': 0.25},
            'mem_graph': {'nodes': [{'id': 8, 'text': '示例', 'imp': 0.8}], 'edges': []},
            'autonomy': {'focus': {'title': '样书'}},
            'book_shelf': {'样书': {'total': 8, 'pages_read': 2}},
            'hb_log': [{'at': 10, 'action': 'read', 'outcome': 'done'},
                       {'at': 20, 'action': 'read', 'outcome': 'failed'}],
        }
        data = room_api.brain_payload(state, now=30)
        nodes = {node['id']: node for node in data['nodes']}
        self.assertEqual(len(data['regions']), 7)
        self.assertEqual(nodes['e_情绪喜']['w'], 0)
        self.assertEqual(nodes['i_示例']['meta']['weight'], 0.25)
        self.assertEqual(nodes['m_8']['meta']['retention'], 1)
        self.assertEqual(nodes['g_focus']['meta']['page'], 2)
        self.assertEqual(nodes['s_read']['meta']['attempts'], 2)
        self.assertEqual(nodes['s_read']['meta']['completed'], 1)
        self.assertEqual(nodes['p_growth_habit']['label'], '记得先整理书桌')
        self.assertTrue(any(edge['kind'] == 'plan-action' for edge in data['links']))
        json.dumps(data, allow_nan=False)

    def test_password_check_fails_closed_when_missing_or_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test-password'
            with patch.object(room_api, 'PASSWORD_FILE', path):
                self.assertFalse(room_api.password_matches(''))
                path.write_text('', encoding='utf-8')
                self.assertFalse(room_api.password_matches(''))
                path.write_text('example', encoding='utf-8')
                self.assertFalse(room_api.password_matches('wrong'))
                self.assertTrue(room_api.password_matches('example'))
