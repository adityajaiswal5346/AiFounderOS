"""
CEO Agent — Planner

Generates a prioritized daily task list for each specialist agent based on:
- Company goals stored in long-term memory
- Outcomes from the previous day
- Current date / calendar context
"""

from __future__ import annotations

from datetime import date
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from memory.long_term import get_company_profile, get_recent_outcomes

PLANNER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are the CEO of an early-stage startup. Your job is to create a focused,
prioritized task list for today for each of your three department heads:
Marketing, Sales, and Operations.

Company profile:
{company_profile}

Yesterday's outcomes:
{recent_outcomes}

Today's date: {today}

Rules:
- Maximum 3 tasks per agent
- Each task must have a clear success criterion
- Flag any task that requires external approval (e.g., sending emails, publishing content)
- If agents have conflicting resource needs, note them for arbitration

Respond in JSON with the schema:
{{
  "marketing": [{{"task": "...", "priority": 1, "requires_approval": false, "success_criterion": "..."}}],
  "sales": [...],
  "operations": [...]
}}""",
        ),
        ("human", "Generate today's task plan."),
    ]
)


async def generate_daily_tasks(
    llm: ChatOpenAI | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Generate a prioritized daily task list for all specialist agents.

    Returns:
        dict mapping agent names to their task lists
    """
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

    company_profile = await get_company_profile()
    recent_outcomes = await get_recent_outcomes(days=1)

    chain = PLANNER_PROMPT | llm
    response = await chain.ainvoke(
        {
            "company_profile": company_profile,
            "recent_outcomes": recent_outcomes,
            "today": date.today().isoformat(),
        }
    )

    # Parse JSON response
    import json

    content = response.content
    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    return json.loads(content.strip())
