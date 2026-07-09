"""
Operations Agent — Tools

Wraps Notion and Slack MCP clients for task management and communication.
Slack announcements require human approval.
"""

from __future__ import annotations

from langchain_core.tools import tool

from mcp_clients.notion_client import create_notion_task as _create_notion_task
from mcp_clients.notion_client import get_notion_tasks as _get_notion_tasks
from mcp_clients.slack_client import send_slack_message
from guardrails.approval_gate import requires_approval


@tool
async def create_notion_task(
    title: str,
    description: str,
    assignee: str = "",
    due_date: str = "",
) -> str:
    """
    Create a new task in Notion.

    Args:
        title: Task title
        description: Detailed task description
        assignee: Person responsible (name or email)
        due_date: Due date in YYYY-MM-DD format
    """
    result = await _create_notion_task(
        title=title,
        description=description,
        assignee=assignee,
        due_date=due_date,
    )
    return f"Created Notion task '{title}' (ID: {result.get('id', '?')})"


@tool
async def get_notion_tasks(filter_status: str = "in_progress") -> str:
    """
    Get tasks from Notion filtered by status.

    Args:
        filter_status: One of 'not_started', 'in_progress', 'blocked', 'done'
    """
    tasks = await _get_notion_tasks(status=filter_status)
    if not tasks:
        return f"No tasks with status '{filter_status}'"

    lines = [f"Notion tasks ({filter_status}):"]
    for t in tasks:
        due = t.get("due_date", "no due date")
        lines.append(f"  [{t.get('id')}] {t.get('title')} — due {due} — {t.get('assignee', 'unassigned')}")
    return "\n".join(lines)


@tool
async def generate_document(doc_type: str, context: str) -> str:
    """
    Generate an internal business document using AI.

    Args:
        doc_type: Type of document — 'sop', 'meeting_notes', 'project_brief', 'onboarding_guide'
        context: Instructions or raw notes to base the document on
    """
    from langchain_openai import ChatOpenAI
    from agents.operations_agent.prompts import DOCUMENT_GENERATION_PROMPT
    from memory.long_term import get_company_profile

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    chain = DOCUMENT_GENERATION_PROMPT | llm

    company_context = await get_company_profile()
    response = await chain.ainvoke(
        {
            "doc_type": doc_type,
            "context": context,
            "company_context": company_context,
        }
    )
    return response.content


@tool
@requires_approval(
    tool_name="send_slack_notification",
    description="Send a Slack message to a channel",
)
async def send_slack_notification(channel: str, message: str) -> str:
    """
    Send a Slack notification. Announcements REQUIRE HUMAN APPROVAL.

    Args:
        channel: Slack channel name (e.g., '#general', '#ops')
        message: Message text (supports basic Slack markdown)
    """
    result = await send_slack_message(channel=channel, message=message)
    return f"Sent Slack message to {channel}: {result}"


# Tool list exposed to the agent
OPERATIONS_TOOLS = [
    create_notion_task,
    get_notion_tasks,
    generate_document,
    send_slack_notification,
]
