"""
MCP Client — Notion

Create and query tasks in a Notion database via official MCP stdio transport.
Used by the Operations Agent.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
from .mcp_session import list_tools, call_tool

logger = logging.getLogger(__name__)

# Resolve npx command on Windows/Linux or fallback to python FastMCP stdio server
npx_cmd = shutil.which("npx") or shutil.which("npx.cmd")

if npx_cmd:
    NOTION_MCP_COMMAND = npx_cmd
    NOTION_MCP_ARGS = ["-y", "@modelcontextprotocol/server-notion"]
else:
    NOTION_MCP_COMMAND = sys.executable
    NOTION_MCP_ARGS = ["-m", "mcp_clients.notion_mcp_server"]


def _notion_env() -> dict:
    """Prepare environment for the Notion MCP server subprocess."""
    env = os.environ.copy()
    if "NOTION_API_KEY" in env:
        env["NOTION_TOKEN"] = env["NOTION_API_KEY"]
    return env


async def list_notion_tools() -> list[dict]:
    """Discover available tools from the Notion MCP server."""
    logger.info(f"Discovering tools from Notion MCP server ({NOTION_MCP_COMMAND})...")
    return await list_tools(NOTION_MCP_COMMAND, NOTION_MCP_ARGS, _notion_env())


async def call_notion_tool(tool_name: str, tool_input: dict) -> dict:
    """Execute a tool on the Notion MCP server."""
    logger.info(f"Executing Notion MCP tool: {tool_name}")
    return await call_tool(NOTION_MCP_COMMAND, NOTION_MCP_ARGS, _notion_env(), tool_name, tool_input)
