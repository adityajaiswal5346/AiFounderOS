"""
Guardrails — Approval Gate

Tool-layer enforcement for actions that require human review before execution.
This is NOT prompt-based — it intercepts at the function call level.

Usage:
    @tool
    @requires_approval(tool_name="send_email", description="Send a marketing email")
    async def send_marketing_email(to: str, subject: str, body: str) -> str:
        ...

When a decorated tool is called, it:
1. Checks if the action is in the approval-required policy
2. If yes: persists a pending approval record and raises ApprovalPendingError
3. If the approval has already been granted (by the human via API): proceeds
"""

from __future__ import annotations

import functools
import json
import logging
import uuid
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ApprovalPendingError(Exception):
    """Raised when a tool call requires approval before execution."""

    def __init__(self, approval_id: str, tool_name: str, description: str) -> None:
        self.approval_id = approval_id
        self.tool_name = tool_name
        self.description = description
        super().__init__(
            f"Action '{tool_name}' requires human approval (id: {approval_id}). "
            f"Review at /approvals/{approval_id}"
        )


class ApprovalRejectedError(Exception):
    """Raised when a queued approval was rejected by the human."""

    def __init__(self, approval_id: str, tool_name: str) -> None:
        self.approval_id = approval_id
        self.tool_name = tool_name
        super().__init__(f"Action '{tool_name}' was rejected (id: {approval_id})")


async def _persist_approval_request(
    tool_name: str,
    description: str,
    payload: dict[str, Any],
) -> str:
    """Write an approval request to the database and return the approval_id."""
    from db.connection import get_db
    from db.models import Approval

    approval_id = str(uuid.uuid4())

    async with get_db() as db:
        db.add(
            Approval(
                id=approval_id,
                tool_name=tool_name,
                description=description,
                payload=json.dumps(payload),
                status="pending",
            )
        )
        await db.commit()

    logger.info(f"Approval request created: {approval_id} ({tool_name})")
    return approval_id


async def _check_approval_status(approval_id: str) -> str:
    """
    Check the current status of an approval request.

    Returns:
        One of: 'pending', 'approved', 'rejected'
    """
    from db.connection import get_db
    from db.models import Approval
    from sqlalchemy import select

    async with get_db() as db:
        result = await db.execute(
            select(Approval).where(Approval.id == approval_id)
        )
        record = result.scalar_one_or_none()

    if record is None:
        return "pending"
    return record.status


def requires_approval(tool_name: str, description: str) -> Callable:
    """
    Decorator that gates a tool behind human approval.

    Args:
        tool_name: Identifier used in the approval policy lookup
        description: Human-readable description shown in the approval UI
    """
    from guardrails.policies import requires_human_approval

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> Any:
            if not requires_human_approval(tool_name):
                # Policy says no approval needed — execute directly
                return await fn(*args, **kwargs)

            # Build the payload for the approval record
            payload = {
                "args": list(args),
                "kwargs": kwargs,
                "tool_name": tool_name,
            }

            approval_id = await _persist_approval_request(
                tool_name=tool_name,
                description=description,
                payload=payload,
            )

            raise ApprovalPendingError(
                approval_id=approval_id,
                tool_name=tool_name,
                description=description,
            )

        return wrapper

    return decorator
