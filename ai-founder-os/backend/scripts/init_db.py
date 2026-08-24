"""
Script — Initialize Database

Creates all tables defined in db/models.py.
Also ensures the pgvector extension is enabled.

Usage:
    python -m scripts.init_db
    # or from backend/:
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# Allow running from repo root or backend/
# __file__ = backend/scripts/init_db.py
# parent   = backend/scripts/
# parent.parent = backend/
BACKEND_DIR = Path(__file__).parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

from sqlalchemy import text
from db.connection import engine
from db import models  # noqa: F401 — import so all tables register with Base
from db.models import Base


async def init() -> None:
    async with engine.begin() as conn:
        # Enable pgvector extension (safe to run repeatedly)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("✓ pgvector extension enabled")
    print("✓ Tables created successfully")
    print("\nTables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    asyncio.run(init())
