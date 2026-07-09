"""
Marketing Agent — Main Agent Loop

ReAct-style agent that executes marketing tasks:
- Trend research
- Content drafting
- Email outreach (with approval gate)
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agents.marketing_agent.prompts import MARKETING_SYSTEM
from agents.marketing_agent.tools import MARKETING_TOOLS
from memory.long_term import get_company_profile
from memory.short_term import get_current_context
from observability.tracing import get_tracer


async def run_marketing_agent(
    tasks: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    """
    Execute the marketing agent for a given set of tasks.

    Args:
        tasks: List of task dicts from the CEO planner
        run_id: Unique ID for this daily run (used in tracing)

    Returns:
        dict with 'output' (summary string), 'completed_tasks', 'pending_approvals'
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(f"marketing_agent.run:{run_id}"):
        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

        company_context = await get_company_profile()
        current_context = await get_current_context(run_id)

        # Format tasks for the prompt
        task_str = "\n".join(
            f"{i+1}. {t['task']} (priority: {t['priority']})"
            for i, t in enumerate(tasks)
        )

        agent = create_react_agent(
            model=llm,
            tools=MARKETING_TOOLS,
        )

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": MARKETING_SYSTEM.format(
                            company_context=company_context,
                            tasks=task_str,
                        ),
                    },
                    {
                        "role": "user",
                        "content": "Execute today's marketing tasks.",
                    },
                ]
            }
        )

        # Extract final message
        final_message = result["messages"][-1].content

        return {
            "agent": "marketing",
            "run_id": run_id,
            "output": final_message,
            "tasks_given": tasks,
        }
