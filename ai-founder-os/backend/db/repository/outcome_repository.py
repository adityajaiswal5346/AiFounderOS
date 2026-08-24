import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Outcome


async def log_outcome(db: AsyncSession, task_id: str, result_summary: str, success: bool, metrics: dict = None) -> Outcome:
    outcome = Outcome(
        task_id=task_id,
        agent="unknown",  # Added to satisfy not-null constraint
        result_summary=result_summary,
        success=success,
    )
    db.add(outcome)
    await db.commit()
    await db.refresh(outcome)
    return outcome


async def get_recent_outcomes(db: AsyncSession, limit: int = 10) -> list[Outcome]:
    result = await db.execute(select(Outcome).order_by(Outcome.created_at.desc()).limit(limit))
    return list(result.scalars().all())