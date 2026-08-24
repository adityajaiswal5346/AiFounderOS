



import os
import json
from sqlalchemy.ext.asyncio import AsyncSession
from observability.tracing import observe
from langchain_core.messages import SystemMessage, HumanMessage

from llm.provider import get_model
from .schemas import DailyPlan
from .prompts import PLANNER_SYSTEM_PROMPT, build_planning_prompt
from db.repository import task_repository, outcome_repository, memory_repository


async def get_roadmap(db: AsyncSession | None) -> str:
    if not db:
        return "No roadmap set yet."
    try:
        roadmap_memory = await memory_repository.get_latest_memory(db, key="roadmap")
        return roadmap_memory.value if roadmap_memory else "No roadmap set yet."
    except Exception:
        return "No roadmap set yet."


async def get_recent_outcomes_text(db: AsyncSession | None) -> list[str]:
    if not db:
        return []
    try:
        outcomes = await outcome_repository.get_recent_outcomes(db, limit=5)
        return [o.result_summary for o in outcomes]
    except Exception:
        return []


async def get_pending_tasks_text(db: AsyncSession | None) -> list[str]:
    if not db:
        return []
    try:
        pending = await task_repository.get_pending_tasks(db)
        return [f"[{t.agent}] {t.description}" for t in pending]
    except Exception:
        return []


@observe(name="ceo_generate_daily_plan")
async def generate_daily_plan(db: AsyncSession) -> DailyPlan:
    roadmap = await get_roadmap(db)
    outcomes = await get_recent_outcomes_text(db)
    pending = await get_pending_tasks_text(db)

    user_prompt = build_planning_prompt(roadmap, outcomes, pending)

    model = get_model(temperature=0.0)
    structured_llm = model.with_structured_output(DailyPlan)
    
    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ]
    
    plan = await structured_llm.ainvoke(messages)
    return plan

@observe(name="ceo_persist_daily_plan")
async def persist_daily_plan(db: AsyncSession, plan: DailyPlan) -> list:
    created_tasks = []
    for task in plan.tasks:
        created = await task_repository.create_task(
            db,
            agent_name=task.agent_name,
            title=task.title,
            description=task.description,
        )
        created_tasks.append(created)
    return created_tasks
