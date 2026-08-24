import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from .policies import requires_human_approval
from typing import Callable

def requires_approval(tool_name: str, description: str) -> Callable:
    """Legacy decorator stub to allow marketing_agent to import."""
    def decorator(fn: Callable) -> Callable:
        return fn
    return decorator
from db.repository import approval_repository


class ApprovalPending(Exception):
    """Raised when an action is blocked, waiting for human approval."""
    def __init__(self, approval_id: str, tool_name: str):
        self.approval_id = approval_id
        self.tool_name = tool_name
        super().__init__(
            f"Action '{tool_name}' requires approval. Pending approval ID: {approval_id}"
        )

async def check_and_gate(db: AsyncSession, task_id: str, tool_name: str, tool_input: dict):
    if not requires_human_approval(tool_name):
        return

    existing = await approval_repository.get_approval_for_task(db, task_id, tool_name)
    if existing and existing.status == "approved":
        return  # already approved, safe to proceed

    if existing and existing.status == "pending":
        raise ApprovalPending(approval_id=existing.id, tool_name=tool_name)

    approval = await approval_repository.create_approval(db, task_id, tool_name, tool_input)
    raise ApprovalPending(approval_id=approval.id, tool_name=tool_name)