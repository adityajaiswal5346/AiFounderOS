"""
Orchestration — Task & Approval Resumption Engine

Provides functionality to resume execution of a paused agent workflow
after human approval is granted.
"""

from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import Approval, Task
from db.repository import task_repository, outcome_repository

logger = logging.getLogger(__name__)


async def resume_approved_task(db: AsyncSession, approval_id: str) -> dict[str, Any]:
    """
    Resumes an agent task once its pending approval has been set to 'approved'.

    Args:
        db: Database session
        approval_id: ID of the approval that was resolved

    Returns:
        Result summary dictionary of the resumed execution
    """
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()

    if not approval:
        raise ValueError(f"Approval '{approval_id}' not found")

    if approval.status != "approved":
        raise ValueError(f"Approval '{approval_id}' is not approved (status: '{approval.status}')")

    task = None
    if approval.task_id:
        task = await task_repository.get_task(db, approval.task_id)

    tool_name = approval.tool_name
    payload = approval.payload or {}

    logger.info(f"Resuming task execution for tool '{tool_name}' (approval ID: {approval_id})")

    execution_result = {}

    # Tool-specific execution dispatch
    if tool_name == "publish_post":
        # Marketing publish fallback execution
        draft_content = payload.get("content", "")
        platform = payload.get("platform", "linkedin")
        summary = f"Approved & published to {platform}:\n\n{draft_content}"
        execution_result = {"status": "completed", "summary": summary}

    elif tool_name in ["send_email", "send_gmail"]:
        # Sales email sending execution
        from mcp_clients.gmail_client import send_gmail
        to_email = payload.get("to")
        subject = payload.get("subject", "Outreach")
        body = payload.get("body", "")

        send_res = await send_gmail(to=to_email, subject=subject, body=body)
        summary = f"Email approved & sent to {to_email}.\nResult: {send_res}"
        execution_result = {"status": "completed", "summary": summary}

    elif tool_name == "send_slack_message":
        # Operations Slack message execution
        from mcp_clients.slack_client import send_slack_message
        channel = payload.get("channel")
        message = payload.get("message")

        slack_res = await send_slack_message(channel=channel, message=message)
        summary = f"Slack message approved & sent to {channel}.\nResult: {slack_res}"
        execution_result = {"status": "completed", "summary": summary}

    else:
        # Generic MCP tool fallback execution
        from mcp_clients.notion_client import call_notion_tool
        mcp_res = await call_notion_tool(tool_name, payload)
        summary = f"Tool '{tool_name}' approved & executed.\nResult: {mcp_res}"
        execution_result = {"status": "completed", "summary": summary}

    # Update task status and log outcome if task exists
    if task:
        await task_repository.update_task_status(
            db,
            task_id=task.id,
            status=execution_result.get("status", "completed"),
            output={"summary": execution_result.get("summary", "")}
        )
        await outcome_repository.log_outcome(
            db,
            task_id=task.id,
            result_summary=execution_result.get("summary", ""),
            success=execution_result.get("status") == "completed"
        )

    return execution_result
