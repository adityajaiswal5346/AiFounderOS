"""
Orchestration — LangGraph Daily Execution Graph

Wires the CEO agent and all specialist agents into a directed execution graph.
State flows: plan → [marketing, sales, operations] (parallel) → arbitrate → digest
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from agents.ceo_agent import generate_daily_plan, arbitrate_conflicts, synthesize_digest
from agents.ceo_agent.conflict_detection import detect_conflicts
from agents.operations_agent import run_operations_task
from db.models import upsert_task_run


class DailyRunState(TypedDict):
    run_id: str
    plan: dict[str, list[dict[str, Any]]]
    marketing_output: dict[str, Any]
    sales_output: dict[str, Any]
    operations_output: dict[str, Any]
    conflicts: list[dict[str, Any]]
    resolutions: list[dict[str, Any]]
    digest: dict[str, str]
    pending_approvals: list[dict[str, Any]]
    errors: list[str]


# ── Node functions ─────────────────────────────────────────────────────────────

async def plan_node(state: DailyRunState) -> DailyRunState:
    """CEO planner generates daily tasks for all agents."""
    try:
        from db.connection import get_db
        from agents.ceo_agent.graph import build_ceo_graph
        from observability.tracing import get_langfuse_callback
        
        ceo_graph = build_ceo_graph()
        
        async with get_db() as db:
            cb = get_langfuse_callback()
            config = {"callbacks": [cb]} if cb else {}
            
            final_ceo_state = await ceo_graph.ainvoke({
                "db": db,
                "run_id": state["run_id"],
                "plan": None,
                "created_tasks": [],
                "errors": []
            }, config=config)
            
            plan = final_ceo_state.get("plan")
            if not plan:
                return {**state, "errors": state.get("errors", []) + final_ceo_state.get("errors", [])}
            
            plan_dict = {}
            for task in plan.tasks:
                agent = task.agent_name.replace("_agent", "")
                if agent not in plan_dict:
                    plan_dict[agent] = []
                plan_dict[agent].append({
                    "task": task.title, 
                    "priority": 1, 
                    "description": task.description
                })
                
            from db.models import upsert_task_run
            await upsert_task_run(run_id=state["run_id"], status="planned", data=plan_dict)
            return {"plan": plan_dict}
    except Exception as e:
        return {"errors": [f"plan_node: {e}"]}


async def marketing_node(state: DailyRunState) -> DailyRunState:
    """Run the marketing agent with its assigned tasks."""
    try:
        from db.connection import get_db
        from agents.marketing_agent.agent import run_all_pending_marketing_tasks
        
        async with get_db() as db:
            outputs = await run_all_pending_marketing_tasks(db)
            return {"marketing_output": {"output": outputs}}
    except Exception as e:
        return {"errors": [f"marketing_node: {e}"]}


async def sales_node(state: DailyRunState) -> DailyRunState:
    """Run the sales agent with its assigned tasks."""
    try:
        from db.connection import get_db
        from agents.sales_agent.agent import run_all_pending_sales_tasks
        
        async with get_db() as db:
            outputs = await run_all_pending_sales_tasks(db)
            return {"sales_output": {"output": outputs}}
    except Exception as e:
        return {"errors": [f"sales_node: {e}"]}


async def operations_node(state: DailyRunState) -> DailyRunState:
    """Run the operations agent with its assigned tasks."""
    try:
        from db.connection import get_db
        from db.repository import task_repository
        
        async with get_db() as db:
            tasks = await task_repository.get_tasks_by_agent(db, agent_name="operations", status="pending")
            outputs = []
            for task in tasks:
                output = await run_operations_task(db, task)
                outputs.append(output)
                
            return {"operations_output": {"output": outputs}}
    except Exception as e:
        return {"errors": [f"operations_node: {e}"]}


async def conflict_detection_node(state: DailyRunState) -> DailyRunState:
    """Detect conflicts from the outputs of specialist agents."""
    try:
        conflicts = await detect_conflicts(
            agent_outputs={
                "marketing": state.get("marketing_output", {}).get("output", ""),
                "sales": state.get("sales_output", {}).get("output", ""),
                "operations": state.get("operations_output", {}).get("output", ""),
            }
        )
        return {"conflicts": conflicts}
    except Exception as e:
        return {"errors": [f"conflict_detection_node: {e}"]}


async def arbitration_node(state: DailyRunState) -> DailyRunState:
    """Detect and resolve any inter-agent conflicts."""
    conflicts = state.get("conflicts", [])
    if not conflicts:
        return state

    try:
        resolutions = await arbitrate_conflicts(conflicts)
        return {"resolutions": resolutions}
    except Exception as e:
        return {"errors": [f"arbitration_node: {e}"]}


async def digest_node(state: DailyRunState) -> DailyRunState:
    """CEO synthesizes the daily digest from all agent outputs."""
    try:
        digest = await synthesize_digest(
            agent_outputs={
                "marketing": state.get("marketing_output", {}).get("output", ""),
                "sales": state.get("sales_output", {}).get("output", ""),
                "operations": state.get("operations_output", {}).get("output", ""),
            },
            pending_approvals=state.get("pending_approvals", []),
            conflicts=state.get("conflicts", []),
            resolutions=state.get("resolutions", [])
        )
        await upsert_task_run(run_id=state["run_id"], status="complete", data=digest)
        return {"digest": digest}
    except Exception as e:
        return {"errors": [f"digest_node: {e}"]}


# ── Graph construction ─────────────────────────────────────────────────────────

def build_daily_graph() -> StateGraph:
    """Build and compile the daily execution graph."""
    graph = StateGraph(DailyRunState)

    graph.add_node("plan", plan_node)
    graph.add_node("marketing", marketing_node)
    graph.add_node("sales", sales_node)
    graph.add_node("operations", operations_node)
    graph.add_node("conflict_detection", conflict_detection_node)
    graph.add_node("arbitration", arbitration_node)
    graph.add_node("digest", digest_node)

    # Edges
    graph.set_entry_point("plan")
    graph.add_edge("plan", "marketing")
    graph.add_edge("plan", "sales")
    graph.add_edge("plan", "operations")
    graph.add_edge("marketing", "conflict_detection")
    graph.add_edge("sales", "conflict_detection")
    graph.add_edge("operations", "conflict_detection")
    graph.add_edge("conflict_detection", "arbitration")
    graph.add_edge("arbitration", "digest")
    graph.add_edge("digest", END)

    return graph.compile()


# Singleton compiled graph
daily_graph = build_daily_graph()
