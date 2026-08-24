"""
Notion MCP Server — Stdio Server Implementation
Standard Model Context Protocol server exposing Notion tools over stdio transport.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Notion")


@mcp.tool()
async def create_notion_task(title: str, description: str = "", assignee: str = "", due_date: str = "") -> dict:
    """Create a task in Notion."""
    return {
        "status": "success",
        "action": "create_notion_task",
        "task_id": "notion_task_123",
        "title": title,
        "description": description,
        "assignee": assignee,
        "due_date": due_date,
    }


@mcp.tool()
async def get_notion_tasks(filter_status: str = "") -> list[dict]:
    """Retrieve tasks from Notion by status filter."""
    return [
        {
            "id": "notion_task_101",
            "title": "Q2 Planning",
            "status": "in_progress" if not filter_status else filter_status,
            "due_date": "2026-08-30",
        }
    ]


@mcp.tool()
async def update_notion_task(task_id: str, status: str = "") -> dict:
    """Update a task status in Notion."""
    return {"status": "success", "task_id": task_id, "updated_status": status}


@mcp.tool()
async def append_notion_page(page_id: str, content: str = "") -> dict:
    """Append text content to a Notion page."""
    return {"status": "success", "page_id": page_id, "content_length": len(content)}


if __name__ == "__main__":
    mcp.run()
