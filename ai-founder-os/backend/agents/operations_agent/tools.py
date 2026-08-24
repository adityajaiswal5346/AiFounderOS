from mcp_clients.notion_client import list_notion_tools, call_notion_tool
from mcp_clients.slack_client import send_slack_message
from mcp_clients.tool_adapter import mcp_tools_to_dict
from guardrails.approval_gate import check_and_gate
from observability.tracing import observe


async def get_tool_definitions() -> list[dict]:
    """Fetches the live tool list from the Notion MCP server, mapped to LangChain tools."""
    try:
        raw_mcp_tools = await list_notion_tools()
        tools = mcp_tools_to_dict(raw_mcp_tools)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to fetch Notion MCP tools: {e}")
        tools = []
        
    slack_tool = {
        "type": "function",
        "function": {
            "name": "send_slack_message",
            "description": "Send a message to a Slack channel",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "Channel name (e.g. #general) or ID"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message text"
                    }
                },
                "required": ["channel", "message"]
            }
        }
    }
    tools.append(slack_tool)
    return tools


@observe(name="operations_execute_tool")
async def execute_tool(db, task_id, tool_name: str, tool_input: dict) -> dict:
    """Dispatches a tool call to the real MCP server — but only after checking approval."""
    await check_and_gate(db, task_id, tool_name, tool_input)  # raises ApprovalPending if blocked
    
    if tool_name == "send_slack_message":
        return await send_slack_message(
            channel=tool_input["channel"],
            message=tool_input["message"]
        )
        
    return await call_notion_tool(tool_name, tool_input)