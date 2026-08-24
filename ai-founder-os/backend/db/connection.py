"""
Database — Connection Management

Async SQLAlchemy session factory backed by asyncpg.
Engine is built lazily on first use so that scripts can call load_dotenv()
before this module reads DATABASE_URL from the environment.
"""

from __future__ import annotations

import os
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)


def _build_url() -> str:
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/ai_founder_os",
    )
    # Heroku-style postgres:// → postgresql+asyncpg://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


# ── Lazy singletons ────────────────────────────────────────────────────────────
_lock = threading.Lock()
_engine: AsyncEngine | None = None
_SessionLocal: async_sessionmaker | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                _engine = create_async_engine(
                    _build_url(),
                    echo=False,
                    pool_size=10,
                    max_overflow=20,
                )
    return _engine


def _get_session_local() -> async_sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        with _lock:
            if _SessionLocal is None:
                _SessionLocal = async_sessionmaker(
                    _get_engine(),
                    class_=AsyncSession,
                    expire_on_commit=False,
                )
    return _SessionLocal


# ── Public proxy so callers can use `engine.begin()` etc. ─────────────────────

class _EngineProxy:
    """Defers real engine creation until first use."""

    def begin(self):
        return _get_engine().begin()

    def connect(self):
        return _get_engine().connect()

    def dispose(self):
        return _get_engine().dispose()

    def __getattr__(self, name: str):
        return getattr(_get_engine(), name)


engine = _EngineProxy()


# ── Session context manager ────────────────────────────────────────────────────

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Usage:
        async with get_db() as db:
            result = await db.execute(...)
            await db.commit()
    """
    async with _get_session_local()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
