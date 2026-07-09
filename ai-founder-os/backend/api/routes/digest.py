"""
API Route — /api/digest

Endpoints for retrieving the daily digest and run history.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, desc

from api.schemas import DigestResponse, DigestListItem
from db.connection import get_db
from db.models import TaskRun

router = APIRouter()


@router.get("/latest", response_model=DigestResponse)
async def get_latest_digest():
    """Get the most recent daily digest."""
    async with get_db() as db:
        result = await db.execute(
            select(TaskRun)
            .where(TaskRun.status == "complete")
            .order_by(desc(TaskRun.created_at))
            .limit(1)
        )
        run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(status_code=404, detail="No completed runs found")

    data = run.data or {}
    digest = data.get("digest", {})

    return DigestResponse(
        run_id=run.run_id,
        date=digest.get("date", run.created_at.date().isoformat()),
        markdown=digest.get("markdown", "No digest available"),
        pending_approval_count=digest.get("pending_approval_count", 0),
        created_at=run.created_at,
    )


@router.get("/history", response_model=list[DigestListItem])
async def get_digest_history(limit: int = 7):
    """Get the last N daily digests."""
    async with get_db() as db:
        result = await db.execute(
            select(TaskRun)
            .where(TaskRun.status == "complete")
            .order_by(desc(TaskRun.created_at))
            .limit(limit)
        )
        runs = result.scalars().all()

    return [
        DigestListItem(
            run_id=r.run_id,
            date=(r.data or {}).get("digest", {}).get("date", r.created_at.date().isoformat()),
            pending_approval_count=(r.data or {}).get("digest", {}).get("pending_approval_count", 0),
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get("/{run_id}", response_model=DigestResponse)
async def get_digest_by_run(run_id: str):
    """Get the digest for a specific run."""
    async with get_db() as db:
        result = await db.execute(
            select(TaskRun).where(TaskRun.run_id == run_id)
        )
        run = result.scalar_one_or_none()

    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    data = run.data or {}
    digest = data.get("digest", {})

    return DigestResponse(
        run_id=run.run_id,
        date=digest.get("date", run.created_at.date().isoformat()),
        markdown=digest.get("markdown", "No digest available"),
        pending_approval_count=digest.get("pending_approval_count", 0),
        created_at=run.created_at,
    )
