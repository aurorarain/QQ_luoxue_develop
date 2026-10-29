"""Compatibility guard loaded on every plugin startup, including container rebuilds."""
import functools

def install_runner_guard():
    from astrbot.core.agent.runners.tool_loop_agent_runner import ToolLoopAgentRunner
    original=ToolLoopAgentRunner.reset
    if getattr(original,'_luoxue_no_tools_guard',False):return
    @functools.wraps(original)
    async def reset(self,*args,**kwargs):
        # Preserve the original public signature via wraps. AstrBot calls reset with keywords.
        request=kwargs.get('request') or (args[1] if len(args)>1 else None)
        if request is not None and not getattr(request,'func_tool',None):
            kwargs['tool_schema_mode']='full'
        await original(self,*args,**kwargs)
    reset._luoxue_no_tools_guard=True
    ToolLoopAgentRunner.reset=reset
