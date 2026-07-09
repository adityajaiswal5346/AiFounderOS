"""
Sales Agent — Main Agent Loop

ReAct-style agent that executes sales tasks:
- Pipeline review and updates
- Personalized outreach drafting
- Email sends (with approval gate)
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agents.sales_agent.prompts import SALES_SYSTEM
from agents.sales_agent.tools import SALES_TOOLS
from memory.long_term import get_company_profile
from observability.tracing import get_tracer


async def run_sales_agent(
    tasks: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    """
    Execute the sales agent for a given set of tasks.

    Args:
        tasks: List of task dicts from the CEO planner
        run_id: Unique ID for this daily run (used in tracing)

    Returns:
        dict with 'output' (summary string), 'completed_tasks', 'pending_approvals'
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(f"sales_agent.run:{run_id}"):
        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        company_context = await get_company_profile()

        task_str = "\n".join(
            f"{i+1}. {t['task']} (priority: {t['priority']})"
            for i, t in enumerate(tasks)
        )

        agent = create_react_agent(
            model=llm,
            tools=SALES_TOOLS,
        )

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": SALES_SYSTEM.format(
                            company_context=company_context,
                            tasks=task_str,
                        ),
                    },
                    {
                        "role": "user",
                        "content": "Execute today's sales tasks.",
                    },
                ]
            }
        )

        final_message = result["messages"][-1].content

        return {
            "agent": "sales",
            "run_id": run_id,
            "output": final_message,
            "tasks_given": tasks,
        }
