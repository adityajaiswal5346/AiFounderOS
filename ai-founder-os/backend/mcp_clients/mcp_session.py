from contextlib import asynccontextmanager
import shutil
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def mcp_session(command: str, args: list[str], env: dict):
    """Generic stdio MCP session — launches ANY MCP server subprocess
    and opens a client connection to it. Used by every agent's MCP client."""
    resolved_cmd = shutil.which(command) or shutil.which(f"{command}.cmd") or command
    params = StdioServerParameters(command=resolved_cmd, args=args, env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def list_tools(command: str, args: list[str], env: dict) -> list[dict]:
    async with mcp_session(command, args, env) as session:
        response = await session.list_tools()
        return [
            {"name": t.name, "description": t.description, "input_schema": t.inputSchema}
            for t in response.tools
        ]


async def call_tool(command: str, args: list[str], env: dict, tool_name: str, tool_input: dict) -> dict:
    async with mcp_session(command, args, env) as session:
        result = await session.call_tool(tool_name, tool_input)
        return {"content": [b.text for b in result.content if hasattr(b, "text")]}