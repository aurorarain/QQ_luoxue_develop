import types
import unittest

class RuntimeRunner(unittest.IsolatedAsyncioTestCase):
    async def test_real_runner_completes_empty_tools_request(self):
        try:
            from astrbot.core.agent.runners.tool_loop_agent_runner import ToolLoopAgentRunner
            from astrbot.core.provider.entities import ProviderRequest,LLMResponse
            from astrbot.core.agent.hooks import BaseAgentRunHooks
        except ImportError:self.skipTest('AstrBot runtime required')
        from luoxue_social.runtime_guard import install_runner_guard
        original=ToolLoopAgentRunner.reset
        try:
            install_runner_guard()
            for mode in ('skills_like','full'):
                calls=[]
                async def text_chat(**kwargs):
                    calls.append(kwargs)
                    return LLMResponse(role='assistant',completion_text='在呢，老大。')
                provider=types.SimpleNamespace(provider_config={'id':'test','max_context_tokens':0},text_chat=text_chat)
                runner=ToolLoopAgentRunner.__new__(ToolLoopAgentRunner)
                request=ProviderRequest(prompt='群友@洛雪',system_prompt='只回复一句话。',func_tool=None)
                context=types.SimpleNamespace(messages=[],context=types.SimpleNamespace(event=None))
                await runner.reset(provider=provider,request=request,run_context=context,tool_executor=None,
                                   agent_hooks=BaseAgentRunHooks(),tool_schema_mode=mode)
                self.assertGreater(runner.stats.start_time,0)
                results=[response async for response in runner.step()]
                self.assertEqual(len(calls),1)
                self.assertTrue(results)
                self.assertEqual(runner.final_llm_resp.completion_text,'在呢，老大。')
        finally:ToolLoopAgentRunner.reset=original
