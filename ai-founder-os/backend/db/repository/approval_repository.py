import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Approval
from datetime import datetime

async def create_approval(db: AsyncSession, task_id: str, tool_name: str, payload: dict, description: str = "") -> Approval:
    approval = Approval(
        id=str(uuid.uuid4()),
        task_id=task_id,
        tool_name=tool_name,
        payload=payload,
        description=description,
        status="pending",
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    return approval

async def get_pending_approvals(db: AsyncSession) -> list[Approval]:
    result = await db.execute(select(Approval).where(Approval.status == "pending"))
    return list(result.scalars().all())

async def get_approval_for_task(db: AsyncSession, task_id: str, tool_name: str) -> Approval | None:
    result = await db.execute(
        select(Approval).where(Approval.task_id == task_id, Approval.tool_name == tool_name)
    )
    return result.scalar_one_or_none()

async def resolve_approval(db: AsyncSession, approval_id: str, approved: bool, reviewed_by: str = None) -> Approval:
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise ValueError(f"Approval {approval_id} not found")
    approval.status = "approved" if approved else "rejected"
    approval.reviewed_at = datetime.utcnow()
    approval.reviewed_by = reviewed_by
    await db.commit()
    await db.refresh(approval)
    return approval

async def is_action_approved(db: AsyncSession, approval_id: str) -> bool:
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    return approval is not None and approval.status == "approved"