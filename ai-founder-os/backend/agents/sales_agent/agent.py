"""
Sales Agent — Main Agent Loop

Phase 6 V1 Sales execution via LangGraph.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from observability.tracing import observe
from db.repository import task_repository, outcome_repository
from db.models import Task

from .graph import build_sales_graph

sales_graph = build_sales_graph()

@observe(name="sales_run_task")
async def run_sales_task(db: AsyncSession, task: Task) -> dict:
    """Runs the LangGraph workflow for a single Sales task."""
    
    from observability.tracing import get_langfuse_callback
    config = {}
    cb = get_langfuse_callback()
    if cb:
        config["callbacks"] = [cb]
        
    try:
        final_state = await sales_graph.ainvoke({
            "db": db,
            "task": task,
            "status": "running",
            "summary": "",
            "leads": [],
            "current_lead": {},
            "qualification": {},
            "draft_email": {}
        }, config=config)
        
        return {
            "status": final_state["status"],
            "summary": final_state["summary"]
        }
    except Exception as e:
        if type(e).__name__ == "GraphRecursionError":
            return {"status": "incomplete", "summary": "Max iterations reached."}
        raise e

@observe(name="sales_run_all_pending")
async def run_all_pending_sales_tasks(db: AsyncSession):
    tasks = await task_repository.get_tasks_by_agent(db, agent_name="sales", status="pending")
    results = []

    for task in tasks:
        result = await run_sales_task(db, task)
        await task_repository.update_task_status(
            db, task.id, status=result["status"], output={"summary": result["summary"]}
        )
        if result["status"] == "completed":
            await outcome_repository.log_outcome(
                db, task_id=task.id, result_summary=result["summary"],
                success=True,
            )
        results.append(result)

    return results
