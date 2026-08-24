"""
API Route — /api/tasks

Endpoints for listing, querying, creating, and tracking agent tasks.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException

from api.schemas import TaskItem, TaskCreateRequest, TaskListResponse
from db.connection import get_db
from db.repository import task_repository

router = APIRouter()


@router.get("", response_model=TaskListResponse)
async def list_tasks(agent: Optional[str] = None, status: Optional[str] = None):
    """List tasks with optional agent and status filtering."""
    async with get_db() as db:
        if agent:
            tasks = await task_repository.get_tasks_by_agent(db, agent_name=agent, status=status)
        elif status == "pending":
            tasks = await task_repository.get_pending_tasks(db)
        else:
            from sqlalchemy import select
            from db.models import Task
            query = select(Task).order_by(Task.created_at.desc())
            if status:
                query = query.where(Task.status == status)
            result = await db.execute(query)
            tasks = list(result.scalars().all())

    items = [
        TaskItem(
            id=t.id,
            run_id=t.run_id,
            agent=t.agent,
            description=t.description,
            status=t.status,
            priority=t.priority,
            requires_approval=t.requires_approval,
            notes=t.notes,
            created_at=t.created_at,
            completed_at=t.completed_at,
        )
        for t in tasks
    ]
    return TaskListResponse(items=items, total=len(items))


@router.get("/{task_id}", response_model=TaskItem)
async def get_task(task_id: str):
    """Get a single task by ID."""
    async with get_db() as db:
        task = await task_repository.get_task(db, task_id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    return TaskItem(
        id=task.id,
        run_id=task.run_id,
        agent=task.agent,
        description=task.description,
        status=task.status,
        priority=task.priority,
        requires_approval=task.requires_approval,
        notes=task.notes,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


@router.post("", response_model=TaskItem)
async def create_task(body: TaskCreateRequest):
    """Create and queue a new agent task."""
    async with get_db() as db:
        task = await task_repository.create_task(
            db,
            agent_name=body.agent_name,
            title=body.title,
            description=body.description
        )

    return TaskItem(
        id=task.id,
        run_id=task.run_id,
        agent=task.agent,
        description=task.description,
        status=task.status,
        priority=task.priority,
        requires_approval=task.requires_approval,
        notes=task.notes,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )
