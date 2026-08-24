"""
API — FastAPI Application

Main app entry point. Mounts routers, configures lifespan events,
and starts the scheduler.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

from api.routes import digest, approvals, roadmap, memory, tasks
from orchestration.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start/stop the APScheduler on app startup/shutdown."""
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="AI Founder OS",
    description="Autonomous multi-agent OS for early-stage startups",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(digest.router, prefix="/api/digest", tags=["digest"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["approvals"])
app.include_router(roadmap.router, prefix="/api/roadmap", tags=["roadmap"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/run-cycle")
async def trigger_daily_cycle():
    """Manually trigger the daily agent cycle (for demo / testing)."""
    from orchestration.scheduler import run_daily_cycle
    import asyncio

    asyncio.create_task(run_daily_cycle())
    return {"message": "Daily cycle started"}
