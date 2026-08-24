"""
API Route — /api/approvals

Endpoints for reviewing and acting on the approval queue.
Integrates with the orchestration resumption engine to resume execution when approved.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException

from api.schemas import ApprovalItem, ApprovalDecision, ApprovalListResponse
from db.connection import get_db
from db.repository import approval_repository
from orchestration.resume import resume_approved_task

router = APIRouter()


@router.get("/pending", response_model=ApprovalListResponse)
async def get_pending_approvals():
    """Get all approvals awaiting human review."""
    async with get_db() as db:
        approvals = await approval_repository.get_pending_approvals(db)

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
        approval = await approval_repository.resolve_approval(db, approval_id, approved=True) # or fetch directly
        # Fetching directly via session
        from sqlalchemy import select
        from db.models import Approval
        result = await db.execute(select(Approval).where(Approval.id == approval_id))
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
    
    If 'approved', asynchronously triggers task resumption and tool execution.
    If 'rejected', marks action as blocked.
    """
    is_approved = (body.decision == "approved")
    async with get_db() as db:
        try:
            approval = await approval_repository.resolve_approval(
                db,
                approval_id=approval_id,
                approved=is_approved,
                reviewed_by=body.reviewed_by or "founder"
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        if is_approved:
            # Trigger task resumption and tool completion
            asyncio.create_task(resume_approved_task(db, approval_id))

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
