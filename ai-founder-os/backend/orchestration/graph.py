"""
Orchestration — LangGraph Daily Execution Graph

Wires the CEO agent and all specialist agents into a directed execution graph.
State flows: plan → [marketing, sales, operations] (parallel) → arbitrate → digest
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from agents.ceo_agent import generate_daily_tasks, arbitrate_conflicts, synthesize_digest
from agents.marketing_agent import run_marketing_agent
from agents.sales_agent import run_sales_agent
from agents.operations_agent import run_operations_agent
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
        plan = await generate_daily_tasks()
        await upsert_task_run(run_id=state["run_id"], status="planned", data=plan)
        return {**state, "plan": plan}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [f"plan_node: {e}"]}


async def marketing_node(state: DailyRunState) -> DailyRunState:
    """Run the marketing agent with its assigned tasks."""
    tasks = state["plan"].get("marketing", [])
    try:
        output = await run_marketing_agent(tasks=tasks, run_id=state["run_id"])
        return {**state, "marketing_output": output}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [f"marketing_node: {e}"]}


async def sales_node(state: DailyRunState) -> DailyRunState:
    """Run the sales agent with its assigned tasks."""
    tasks = state["plan"].get("sales", [])
    try:
        output = await run_sales_agent(tasks=tasks, run_id=state["run_id"])
        return {**state, "sales_output": output}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [f"sales_node: {e}"]}


async def operations_node(state: DailyRunState) -> DailyRunState:
    """Run the operations agent with its assigned tasks."""
    tasks = state["plan"].get("operations", [])
    try:
        output = await run_operations_agent(tasks=tasks, run_id=state["run_id"])
        return {**state, "operations_output": output}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [f"operations_node: {e}"]}


async def arbitration_node(state: DailyRunState) -> DailyRunState:
    """Detect and resolve any inter-agent conflicts."""
    conflicts = state.get("conflicts", [])
    if not conflicts:
        return state

    try:
        resolutions = await arbitrate_conflicts(conflicts)
        return {**state, "resolutions": resolutions}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [f"arbitration_node: {e}"]}


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
        )
        await upsert_task_run(run_id=state["run_id"], status="complete", data=digest)
        return {**state, "digest": digest}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [f"digest_node: {e}"]}


# ── Graph construction ─────────────────────────────────────────────────────────

def build_daily_graph() -> StateGraph:
    """Build and compile the daily execution graph."""
    graph = StateGraph(DailyRunState)

    graph.add_node("plan", plan_node)
    graph.add_node("marketing", marketing_node)
    graph.add_node("sales", sales_node)
    graph.add_node("operations", operations_node)
    graph.add_node("arbitration", arbitration_node)
    graph.add_node("digest", digest_node)

    # Edges
    graph.set_entry_point("plan")
    graph.add_edge("plan", "marketing")
    graph.add_edge("plan", "sales")
    graph.add_edge("plan", "operations")
    graph.add_edge("marketing", "arbitration")
    graph.add_edge("sales", "arbitration")
    graph.add_edge("operations", "arbitration")
    graph.add_edge("arbitration", "digest")
    graph.add_edge("digest", END)

    return graph.compile()


# Singleton compiled graph
daily_graph = build_daily_graph()
