"""Synthetic search responses; no live credentials or conversations."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import test_boundaries
from luoxue_social import features, web_search
from test_brain_api import room_api


class SearchBudgets(unittest.IsolatedAsyncioTestCase):
    def feature(self, **config):
        return SimpleNamespace(cfg={'web_search': {'tavily_api_key': 'SYNTHETIC_TOKEN', **config}},
                               s=SimpleNamespace(state={}, save=lambda: None))

    async def test_concurrent_duplicate_queries_charge_once(self):
        f = self.feature()
        with patch.object(web_search, '_request', AsyncMock(return_value=[{'url': 'https://example.org'}])) as call:
            results = await asyncio.gather(web_search.search(f, 'python docs'), web_search.search(f, 'python docs'))
        self.assertEqual(call.await_count, 1)
        self.assertTrue(results[1]['cached'])
        self.assertEqual(f.s.state['web_usage_v2']['credits'], 1)

    async def test_failure_reserves_budget_without_leaking_secret(self):
        f = self.feature(daily_limit=1)
        with patch.object(web_search, '_request', AsyncMock(side_effect=RuntimeError('SYNTHETIC_TOKEN'))) as call:
            first = await web_search.search(f, 'python docs')
            second = await web_search.search(f, 'different docs')
        self.assertNotIn('SYNTHETIC_TOKEN', json.dumps(first))
        self.assertIn('上限', second['error'])
        self.assertEqual(call.await_count, 1)

    async def test_monthly_limit_also_prevents_request(self):
        f = self.feature(monthly_limit=1)
        with patch.object(web_search, '_request', AsyncMock(return_value=[])) as call:
            await web_search.search(f, 'python docs')
            result = await web_search.search(f, 'other docs')
        self.assertIn('上限', result['error'])
        self.assertEqual(call.await_count, 1)

    async def test_brave_uses_its_fixed_endpoint_and_header(self):
        f = self.feature(provider='brave', brave_api_key='SYNTHETIC_BRAVE')
        data = {'web': {'results': [{'title': 'Python docs', 'description': 'Python reference', 'url': 'https://example.org'}]}}
        with patch.object(features, 'fetch', AsyncMock(return_value=json.dumps(data).encode())) as call:
            result = await web_search.search(f, 'python docs')
        self.assertEqual(result['provider'], 'Brave')
        self.assertTrue(call.call_args.args[0].startswith('https://api.search.brave.com/'))
        self.assertEqual(call.call_args.kwargs['headers']['X-Subscription-Token'], 'SYNTHETIC_BRAVE')

    def test_irrelevant_and_duplicate_sources_are_removed(self):
        rows = [None, {'title': 'Court judgement', 'content': 'Wildlife law', 'url': 'https://example.org/law'},
                {'title': 'Python docs', 'content': 'Python reference', 'url': 'https://example.org/python'},
                {'title': 'Python docs', 'url': 'https://example.org/python#top'},
                {'title': 'Python docs', 'url': 'javascript:alert(1)'}]
        result = web_search.normalized_results({'results': rows}, 'tavily', 'python docs')
        self.assertEqual([r['url'] for r in result], ['https://example.org/python'])


class SearchConfiguration(unittest.TestCase):
    def test_config_preserves_key_without_ever_returning_it(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(room_api, 'PLUGIN_DIR', directory), patch.object(room_api, 'BOT_STATE', str(Path(directory) / 'state.json')):
            first = room_api.save_search_config({'provider': 'tavily', 'api_key': 'SYNTHETIC_SECRET'})
            second = room_api.save_search_config({'provider': 'tavily', 'daily_limit': 20})
            self.assertTrue(first['configured'])
            self.assertNotIn('SYNTHETIC_SECRET', json.dumps(second))
            config = web_search.settings(SimpleNamespace(cfg={}, root=Path(directory)))
            self.assertEqual(config['key'], 'SYNTHETIC_SECRET')
            self.assertEqual(config['daily_limit'], 20)

    def test_invalid_provider_and_header_injection_are_rejected(self):
        for value in [{'provider': 'arbitrary'}, {'provider': 'tavily', 'api_key': 'a\nb'}, {'provider': 'tavily', 'monthly_limit': 999999}]:
            with self.assertRaises(ValueError):
                room_api.save_search_config(value)
