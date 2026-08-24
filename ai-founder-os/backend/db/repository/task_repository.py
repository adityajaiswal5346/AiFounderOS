import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Task


async def create_task(db: AsyncSession, agent_name: str, title: str, description: str = None) -> Task:
    desc = f"{title}\n\n{description}" if description else title
    task = Task(
        id=str(uuid.uuid4()),
        run_id="default_run",
        agent=agent_name,
        description=desc,
        status="pending",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: str) -> Task | None:
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def get_tasks_by_agent(db: AsyncSession, agent_name: str, status: str = None) -> list[Task]:
    query = select(Task).where(Task.agent == agent_name)
    if status:
        query = query.where(Task.status == status)
    query = query.order_by(Task.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_pending_tasks(db: AsyncSession) -> list[Task]:
    result = await db.execute(select(Task).where(Task.status == "pending"))
    return list(result.scalars().all())


async def update_task_status(db: AsyncSession, task_id: str, status: str, output: dict = None) -> Task:
    task = await get_task(db, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    task.status = status
    if output is not None and hasattr(task, "notes"):
        task.notes = str(output)
    await db.commit()
    await db.refresh(task)
    return task