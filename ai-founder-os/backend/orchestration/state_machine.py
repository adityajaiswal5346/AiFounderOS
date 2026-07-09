"""
Orchestration — Task State Machine

Defines valid task status transitions and enforces them.

States:
  pending → in_progress → awaiting_approval → done
                        ↘ failed
  in_progress → failed
  awaiting_approval → rejected → failed
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from db.connection import get_db
from db.models import Task


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    DONE = "done"
    FAILED = "failed"
    REJECTED = "rejected"


# Valid transitions: current_status → set of allowed next statuses
VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.IN_PROGRESS, TaskStatus.FAILED},
    TaskStatus.IN_PROGRESS: {
        TaskStatus.AWAITING_APPROVAL,
        TaskStatus.DONE,
        TaskStatus.FAILED,
    },
    TaskStatus.AWAITING_APPROVAL: {
        TaskStatus.IN_PROGRESS,  # approved, resuming
        TaskStatus.REJECTED,
        TaskStatus.FAILED,
    },
    TaskStatus.REJECTED: {TaskStatus.FAILED},
    TaskStatus.DONE: set(),  # terminal
    TaskStatus.FAILED: set(),  # terminal
}


class InvalidTransitionError(Exception):
    def __init__(self, current: TaskStatus, requested: TaskStatus) -> None:
        super().__init__(
            f"Invalid transition: {current.value!r} → {requested.value!r}. "
            f"Allowed from {current.value!r}: "
            f"{[s.value for s in VALID_TRANSITIONS[current]]}"
        )


async def transition_task(
    task_id: str,
    new_status: TaskStatus,
    notes: Optional[str] = None,
) -> Task:
    """
    Transition a task to a new status, enforcing valid transition rules.

    Args:
        task_id: Task ID to update
        new_status: Target status
        notes: Optional notes to attach to the transition

    Returns:
        Updated Task object

    Raises:
        InvalidTransitionError: If the transition is not allowed
        ValueError: If task not found
    """
    async with get_db() as db:
        task = await db.get(Task, task_id)
        if task is None:
            raise ValueError(f"Task {task_id!r} not found")

        current = TaskStatus(task.status)
        if new_status not in VALID_TRANSITIONS[current]:
            raise InvalidTransitionError(current, new_status)

        task.status = new_status.value
        if notes:
            task.notes = notes

        await db.commit()
        await db.refresh(task)
        return task


def is_terminal(status: TaskStatus) -> bool:
    """Return True if the status is a terminal state (no further transitions)."""
    return not VALID_TRANSITIONS[status]
