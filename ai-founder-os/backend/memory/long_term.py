"""
Memory — Long-Term Memory

Persistent storage for business profile, past decisions, and outcomes.
Backed by Postgres. Read at the start of each daily run and updated
when significant decisions or outcomes are recorded.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, desc
from db.connection import get_db
from db.models import MemoryLong, Outcome

logger = logging.getLogger(__name__)


async def get_company_profile() -> str:
    """
    Retrieve the company profile from long-term memory.

    Returns:
        Company profile as a formatted string, or a default message if not set.
    """
    async with get_db() as db:
        result = await db.execute(
            select(MemoryLong).where(MemoryLong.key == "company_profile")
        )
        record = result.scalar_one_or_none()

        if record is None:
            logger.warning("Company profile not found in long-term memory. Run seed_onboarding.py.")
            return "No company profile found. Please run seed_onboarding.py to set up."

        return record.value


async def get_recent_outcomes(days: int = 1) -> str:
    """
    Get task outcomes from the past N days, formatted for the planner prompt.

    Args:
        days: Number of days to look back

    Returns:
        Formatted string of recent outcomes
    """
    since = datetime.utcnow() - timedelta(days=days)

    async with get_db() as db:
        result = await db.execute(
            select(Outcome)
            .where(Outcome.created_at >= since)
            .order_by(desc(Outcome.created_at))
            .limit(20)
        )
        outcomes = result.scalars().all()

    if not outcomes:
        return "No outcomes recorded yet."

    lines = []
    for o in outcomes:
        status = "✓" if o.success else "✗"
        lines.append(f"{status} [{o.agent}] {o.result_summary}")
    return "\n".join(lines)


async def save_memory(key: str, value: Any) -> None:
    """
    Save or update a long-term memory entry.

    Args:
        key: Memory key (unique identifier)
        value: Value to store (will be JSON-serialized if not a string)
    """
    if not isinstance(value, str):
        value = json.dumps(value)

    async with get_db() as db:
        result = await db.execute(
            select(MemoryLong).where(MemoryLong.key == key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
            existing.updated_at = datetime.utcnow()
        else:
            db.add(MemoryLong(key=key, value=value))

        await db.commit()


async def get_memory(key: str, default: Any = None) -> Any:
    """
    Retrieve a long-term memory value by key.

    Args:
        key: Memory key
        default: Value to return if key not found

    Returns:
        Stored value (JSON-parsed if possible), or default
    """
    async with get_db() as db:
        result = await db.execute(
            select(MemoryLong).where(MemoryLong.key == key)
        )
        record = result.scalar_one_or_none()

    if record is None:
        return default

    try:
        return json.loads(record.value)
    except (json.JSONDecodeError, TypeError):
        return record.value
