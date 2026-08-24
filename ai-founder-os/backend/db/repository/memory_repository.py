import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import MemoryLong as Memory


async def set_memory(db: AsyncSession, key: str, value: str) -> Memory:
    """Creates or updates a memory entry."""
    result = await db.execute(select(Memory).where(Memory.key == key))
    memory = result.scalar_one_or_none()
    if memory:
        memory.value = value
    else:
        memory = Memory(key=key, value=value)
        db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


async def get_latest_memory(db: AsyncSession, key: str) -> Memory | None:
    result = await db.execute(
        select(Memory).where(Memory.key == key).order_by(Memory.updated_at.desc())
    )
    return result.scalar_one_or_none()


async def get_all_memory(db: AsyncSession) -> list[Memory]:
    result = await db.execute(select(Memory))
    return list(result.scalars().all())