"""
MCP Client — Notion

Create and query tasks in a Notion database.
Used by the Operations Agent.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from notion_client import AsyncClient

logger = logging.getLogger(__name__)


def _get_client() -> AsyncClient:
    return AsyncClient(auth=os.environ["NOTION_API_KEY"])


async def create_notion_task(
    title: str,
    description: str,
    assignee: str = "",
    due_date: str = "",
    database_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a new task page in a Notion database.

    Args:
        title: Task title
        description: Task description (added as a paragraph block)
        assignee: Name of the person responsible
        due_date: ISO 8601 date string (YYYY-MM-DD)
        database_id: Override the default NOTION_DATABASE_ID env var

    Returns:
        Notion API page object
    """
    database_id = database_id or os.environ["NOTION_DATABASE_ID"]
    client = _get_client()

    properties: dict[str, Any] = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Status": {"select": {"name": "Not Started"}},
    }

    if assignee:
        properties["Assignee"] = {"rich_text": [{"text": {"content": assignee}}]}

    if due_date:
        properties["Due Date"] = {"date": {"start": due_date}}

    page = await client.pages.create(
        parent={"database_id": database_id},
        properties=properties,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": description}}]
                },
            }
        ],
    )
    logger.info(f"Created Notion task '{title}' (id: {page['id']})")
    return page


async def get_notion_tasks(
    status: str = "in_progress",
    database_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Query tasks from a Notion database filtered by status.

    Args:
        status: Filter by Status property value
        database_id: Override default NOTION_DATABASE_ID

    Returns:
        List of simplified task dicts
    """
    database_id = database_id or os.environ["NOTION_DATABASE_ID"]
    client = _get_client()

    status_map = {
        "not_started": "Not Started",
        "in_progress": "In Progress",
        "blocked": "Blocked",
        "done": "Done",
    }
    notion_status = status_map.get(status, status)

    response = await client.databases.query(
        database_id=database_id,
        filter={"property": "Status", "select": {"equals": notion_status}},
    )

    tasks = []
    for page in response.get("results", []):
        props = page.get("properties", {})
        tasks.append(
            {
                "id": page["id"],
                "title": (
                    props.get("Name", {})
                    .get("title", [{}])[0]
                    .get("text", {})
                    .get("content", "")
                ),
                "status": props.get("Status", {}).get("select", {}).get("name", ""),
                "assignee": (
                    props.get("Assignee", {})
                    .get("rich_text", [{}])[0]
                    .get("text", {})
                    .get("content", "")
                ),
                "due_date": props.get("Due Date", {}).get("date", {}).get("start", ""),
            }
        )
    return tasks
