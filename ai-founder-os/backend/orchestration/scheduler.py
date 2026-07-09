"""
Orchestration — Scheduler

Triggers the daily execution graph via APScheduler (cron).
Can also be triggered manually via the API or run_daily_cycle.py script.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from orchestration.graph import daily_graph

logger = logging.getLogger(__name__)


async def run_daily_cycle(run_id: str | None = None) -> dict:
    """
    Execute the full daily agent cycle.

    Args:
        run_id: Optional run ID for tracing. Auto-generated if not provided.

    Returns:
        Final graph state dict
    """
    if run_id is None:
        run_id = f"run_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"

    logger.info(f"Starting daily cycle: {run_id}")

    initial_state = {
        "run_id": run_id,
        "plan": {},
        "marketing_output": {},
        "sales_output": {},
        "operations_output": {},
        "conflicts": [],
        "resolutions": [],
        "digest": {},
        "pending_approvals": [],
        "errors": [],
    }

    final_state = await daily_graph.ainvoke(initial_state)

    if final_state.get("errors"):
        logger.warning(f"Daily cycle {run_id} completed with errors: {final_state['errors']}")
    else:
        logger.info(f"Daily cycle {run_id} completed successfully")

    return final_state


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler instance."""
    scheduler = AsyncIOScheduler()

    # Daily cycle at 7:00 AM UTC
    scheduler.add_job(
        run_daily_cycle,
        trigger=CronTrigger(hour=7, minute=0, timezone="UTC"),
        id="daily_cycle",
        name="AI Founder OS Daily Cycle",
        replace_existing=True,
        misfire_grace_time=300,  # 5 min grace window
    )

    return scheduler


# Module-level scheduler instance
scheduler = create_scheduler()
