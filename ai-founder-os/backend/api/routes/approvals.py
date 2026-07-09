"""
API Route — /api/approvals

Endpoints for reviewing and acting on the approval queue.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from api.schemas import ApprovalItem, ApprovalDecision, ApprovalListResponse
from db.connection import get_db
from db.models import Approval

router = APIRouter()


@router.get("/pending", response_model=ApprovalListResponse)
async def get_pending_approvals():
    """Get all approvals awaiting human review."""
    async with get_db() as db:
        result = await db.execute(
            select(Approval)
            .where(Approval.status == "pending")
            .order_by(Approval.created_at)
        )
        approvals = result.scalars().all()

    items = [
        ApprovalItem(
            id=a.id,
            task_id=a.task_id,
            tool_name=a.tool_name,
            description=a.description,
            payload=a.payload,
            status=a.status,
            created_at=a.created_at,
            reviewed_at=a.reviewed_at,
            reviewed_by=a.reviewed_by,
        )
        for a in approvals
    ]
    return ApprovalListResponse(items=items, total=len(items))


@router.get("/{approval_id}", response_model=ApprovalItem)
async def get_approval(approval_id: str):
    """Get a specific approval by ID."""
    async with get_db() as db:
        result = await db.execute(
            select(Approval).where(Approval.id == approval_id)
        )
        approval = result.scalar_one_or_none()

    if approval is None:
        raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found")

    return ApprovalItem(
        id=approval.id,
        task_id=approval.task_id,
        tool_name=approval.tool_name,
        description=approval.description,
        payload=approval.payload,
        status=approval.status,
        created_at=approval.created_at,
        reviewed_at=approval.reviewed_at,
        reviewed_by=approval.reviewed_by,
    )


@router.post("/{approval_id}/decide", response_model=ApprovalItem)
async def decide_approval(approval_id: str, body: ApprovalDecision):
    """
    Approve or reject a queued action.
    
    Setting decision to 'approved' allows the tool to execute on the next agent cycle.
    Setting 'rejected' marks the action as blocked.
    """
    async with get_db() as db:
        result = await db.execute(
            select(Approval).where(Approval.id == approval_id)
        )
        approval = result.scalar_one_or_none()

        if approval is None:
            raise HTTPException(status_code=404, detail=f"Approval '{approval_id}' not found")

        if approval.status != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Approval is already '{approval.status}' — cannot change",
            )

        approval.status = body.decision
        approval.reviewed_at = datetime.utcnow()
        approval.reviewed_by = body.reviewed_by or "founder"

        await db.commit()
        await db.refresh(approval)

    return ApprovalItem(
        id=approval.id,
        task_id=approval.task_id,
        tool_name=approval.tool_name,
        description=approval.description,
        payload=approval.payload,
        status=approval.status,
        created_at=approval.created_at,
        reviewed_at=approval.reviewed_at,
        reviewed_by=approval.reviewed_by,
    )
