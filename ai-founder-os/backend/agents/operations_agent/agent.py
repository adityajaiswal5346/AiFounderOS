import os

from sqlalchemy.ext.asyncio import AsyncSession
from observability.tracing import observe

from .prompts import OPERATIONS_SYSTEM_PROMPT
from .tools import get_tool_definitions, execute_tool
from guardrails.approval_gate import ApprovalPending
from db.repository import task_repository, outcome_repository
from db.models import Task

from langchain_core.messages import SystemMessage, HumanMessage
from .graph import build_ops_graph

MAX_ITERATIONS = 5

ops_graph = build_ops_graph()


@observe(name="operations_run_task")
async def run_operations_task(db: AsyncSession, task: Task) -> dict:
    """Runs the LangGraph ReAct loop for a single Operations task."""
    
    initial_messages = [
        SystemMessage(content=OPERATIONS_SYSTEM_PROMPT),
        HumanMessage(content=f"Task Details: {task.description or 'No additional details.'}")
    ]
    
    # We pass recursion_limit=MAX_ITERATIONS to the config to enforce our old loop limit
    from observability.tracing import get_langfuse_callback
    config = {"recursion_limit": MAX_ITERATIONS}
    
    cb = get_langfuse_callback()
    if cb:
        config["callbacks"] = [cb]
        
    try:
        final_state = await ops_graph.ainvoke({
            "db": db,
            "task": task,
            "messages": initial_messages,
            "status": "running",
            "summary": ""
        }, config=config)
        
        return {
            "status": final_state["status"],
            "summary": final_state["summary"]
        }
    except Exception as e:
        # If it hits recursion limit, it raises GraphRecursionError
        if type(e).__name__ == "GraphRecursionError":
            return {"status": "incomplete", "summary": "Max iterations reached without completion."}
        raise e


@observe(name="operations_run_all_pending")
async def run_all_pending_operations_tasks(db: AsyncSession):
    tasks = await task_repository.get_tasks_by_agent(db, agent_name="operations", status="pending")
    results = []

    for task in tasks:
        result = await run_operations_task(db, task)
        await task_repository.update_task_status(
            db, task.id, status=result["status"], output={"summary": result["summary"]}
        )
        await outcome_repository.log_outcome(
            db, task_id=task.id, result_summary=result["summary"],
            success=(result["status"] == "completed"),
        )
        results.append(result)

    return results