"""
CEO Agent — LangGraph Subgraph

Implements the CEO's planning workflow as a directed state graph.
"""

from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from .planner import generate_daily_plan, persist_daily_plan
from .schemas import DailyPlan


class CEOState(TypedDict):
    db: AsyncSession
    run_id: str
    plan: DailyPlan | None
    created_tasks: list[Any]
    errors: list[str]


async def plan_node(state: CEOState) -> CEOState:
    """Generate the daily plan."""
    try:
        plan = await generate_daily_plan(state["db"])
        return {**state, "plan": plan}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [f"CEO plan_node error: {e}"]}


async def persist_node(state: CEOState) -> CEOState:
    """Persist the plan into tasks in the database."""
    if not state.get("plan"):
        return state

    try:
        tasks = await persist_daily_plan(state["db"], state["plan"])
        return {**state, "created_tasks": tasks}
    except Exception as e:
        return {**state, "errors": state.get("errors", []) + [f"CEO persist_node error: {e}"]}


def build_ceo_graph() -> StateGraph:
    """Compile the CEO state graph."""
    graph = StateGraph(CEOState)

    graph.add_node("plan", plan_node)
    graph.add_node("persist", persist_node)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "persist")
    graph.add_edge("persist", END)

    return graph.compile()
