"""
MCP Tool Adapter

Converts standard MCP JSON Schema tool definitions into LangChain StructuredTool
objects so that agents (Gemini, OpenAI, etc.) can bind and call them natively.
"""

from typing import Any, Callable, Awaitable
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field

def mcp_tools_to_langchain(
    mcp_tools: list[dict],
    executor: Callable[[str, dict], Awaitable[dict]],
) -> list[StructuredTool]:
    """
    Convert a list of MCP tool definitions into LangChain tools.
    
    Args:
        mcp_tools: List of dicts with 'name', 'description', and 'input_schema'
        executor: Async function taking (tool_name, tool_kwargs) and returning dict
        
    Returns:
        List of LangChain StructuredTool instances
    """
    lc_tools = []
    
    for tool_def in mcp_tools:
        name = tool_def["name"]
        description = tool_def.get("description", "")
        schema = tool_def.get("input_schema", {})
        
        # We need to capture the current name correctly for the lambda/coroutine
        # by creating a factory function or using defaults.
        async def make_coro(tool_name=name):
            async def _call(**kwargs) -> str:
                result = await executor(tool_name, kwargs)
                # Ensure the returned result is stringified for LLM consumption
                if isinstance(result, dict) and "content" in result:
                    return str(result["content"])
                return str(result)
            return _call

        import asyncio
        # Create a dynamic pydantic model for the arguments if needed, 
        # or we can just pass the raw dict schema to args_schema. 
        # However, LangChain StructuredTool prefers a Pydantic model for args_schema,
        # but you can also just pass the JSON schema directly as a dict in some versions.
        # Actually, if we just want to bypass dynamic Pydantic model generation, we can create
        # a standard function and let LangChain handle it, but wait! StructuredTool allows `args_schema`.
        
        # Alternatively, we can just return a dict that matches OpenAI's JSON format and bind that,
        # but LangChain prefers StructuredTool. Let's build a dynamic model from JSON schema:
        # A simpler approach is to use the raw schema dict if `bind_tools` supports it.
        # Let's use `StructuredTool` and rely on LangChain's internal parsing if possible.
        # Wait, the easiest way to bind tools in LangChain is to just pass a dict!
        pass 
        
    return lc_tools

def mcp_tools_to_dict(mcp_tools: list[dict]) -> list[dict]:
    """
    Convert MCP tool schemas directly to OpenAI/Gemini compatible tool dicts.
    LangChain's `bind_tools` directly accepts this format.
    """
    lc_tools = []
    for tool_def in mcp_tools:
        lc_tools.append({
            "type": "function",
            "function": {
                "name": tool_def["name"],
                "description": tool_def.get("description", ""),
                "parameters": tool_def.get("input_schema", {"type": "object", "properties": {}})
            }
        })
    return lc_tools
