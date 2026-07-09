"""
Operations Agent — Main Agent Loop

ReAct-style agent that executes operations tasks:
- Notion task creation and status checks
- Document generation (SOPs, briefs, meeting notes)
- Slack notifications (with approval gate)
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agents.operations_agent.prompts import OPERATIONS_SYSTEM
from agents.operations_agent.tools import OPERATIONS_TOOLS
from memory.long_term import get_company_profile
from observability.tracing import get_tracer


async def run_operations_agent(
    tasks: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    """
    Execute the operations agent for a given set of tasks.

    Args:
        tasks: List of task dicts from the CEO planner
        run_id: Unique ID for this daily run (used in tracing)

    Returns:
        dict with 'output' (summary string), 'completed_tasks', 'pending_approvals'
    """
    tracer = get_tracer()

    with tracer.start_as_current_span(f"operations_agent.run:{run_id}"):
        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        company_context = await get_company_profile()

        task_str = "\n".join(
            f"{i+1}. {t['task']} (priority: {t['priority']})"
            for i, t in enumerate(tasks)
        )

        agent = create_react_agent(
            model=llm,
            tools=OPERATIONS_TOOLS,
        )

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": OPERATIONS_SYSTEM.format(
                            company_context=company_context,
                            tasks=task_str,
                        ),
                    },
                    {
                        "role": "user",
                        "content": "Execute today's operations tasks.",
                    },
                ]
            }
        )

        final_message = result["messages"][-1].content

        return {
            "agent": "operations",
            "run_id": run_id,
            "output": final_message,
            "tasks_given": tasks,
        }
