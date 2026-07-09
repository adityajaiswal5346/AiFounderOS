"""
Database — SQLAlchemy Models

Schema for:
- Tasks and task runs
- Approval queue
- Long-term memory (with pgvector embeddings)
- Outcomes (historical task results)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    run_id = Column(String, nullable=False, index=True)
    agent = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, in_progress, awaiting_approval, done, failed
    priority = Column(Integer, default=1)
    requires_approval = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    tool_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryLong(Base):
    __tablename__ = "memory_long"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # text-embedding-3-small dimension
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    agent = Column(String, nullable=False)
    result_summary = Column(Text, nullable=False)
    success = Column(Boolean, default=True)
    trace_id = Column(String, nullable=True)  # Langfuse trace ID
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskRun(Base):
    __tablename__ = "task_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="started")  # started, planned, running, complete, failed
    data = Column(JSON, nullable=True)  # stores the graph final state
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


# ── Helper functions ───────────────────────────────────────────────────────────

async def upsert_task_run(
    run_id: str,
    status: str,
    data: dict[str, Any] | None = None,
) -> TaskRun:
    """Upsert a task run record (used by graph nodes to persist state)."""
    from db.connection import get_db
    from sqlalchemy import select

    async with get_db() as db:
        result = await db.execute(
            select(TaskRun).where(TaskRun.run_id == run_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = status
            if data is not None:
                existing.data = data
            if status == "complete":
                existing.completed_at = datetime.utcnow()
        else:
            db.add(
                TaskRun(
                    run_id=run_id,
                    status=status,
                    data=data,
                )
            )

        await db.commit()
        result = await db.execute(
            select(TaskRun).where(TaskRun.run_id == run_id)
        )
        return result.scalar_one()
