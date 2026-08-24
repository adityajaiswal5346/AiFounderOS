"""
CEO Agent — Conflict Detection

Analyzes agent outcomes to detect meaningful cross-agent conflicts.
"""

from __future__ import annotations

from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from llm.provider import get_model
from observability.tracing import observe


class Conflict(BaseModel):
    description: str = Field(description="Description of the conflict")
    involved_agents: list[str] = Field(description="List of agents involved (e.g. marketing, sales, operations)")
    severity: str = Field(description="low, medium, high")
    recommended_action: str = Field(description="Advisory recommendation for arbitration")

class ConflictReport(BaseModel):
    conflicts: list[Conflict] = Field(default_factory=list, description="List of meaningful conflicts detected. Empty if no conflicts.")


CONFLICT_DETECTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are the CEO's conflict detection module.
Analyze the following daily outcomes from the specialist agents.

Marketing Outcome:
{marketing_output}

Sales Outcome:
{sales_output}

Operations Outcome:
{operations_output}

Your goal is to detect MEANINGFUL CONFLICTS between the agents.
Examples of meaningful conflicts:
- Marketing says campaign X is successful, but Sales says leads from X are terrible.
- Sales wants to onboard a customer immediately, but Operations reports onboarding is blocked.
- Two agents recommend incompatible strategic actions.

Do NOT report trivial differences. Do not report independent failures as conflicts unless they directly contradict another agent's success.
If there are no meaningful conflicts, return an empty list of conflicts.

Return the result as structured JSON."""
        ),
        ("human", "Detect conflicts in today's outcomes."),
    ]
)


@observe(name="ceo_detect_conflicts")
async def detect_conflicts(
    agent_outputs: dict[str, Any],
    llm: BaseChatModel | None = None,
) -> list[dict[str, Any]]:
    """
    Detect conflicts across agent outputs.

    Args:
        agent_outputs: dict with keys 'marketing', 'sales', 'operations'
        llm: Optional chat model

    Returns:
        List of conflict dictionaries
    """
    if llm is None:
        llm = get_model(temperature=0.0)

    structured_llm = llm.with_structured_output(ConflictReport)
    chain = CONFLICT_DETECTION_PROMPT | structured_llm

    try:
        report = await chain.ainvoke(
            {
                "marketing_output": agent_outputs.get("marketing", "No output"),
                "sales_output": agent_outputs.get("sales", "No output"),
                "operations_output": agent_outputs.get("operations", "No output"),
            }
        )
        return [c.model_dump() for c in report.conflicts]
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Conflict detection failed: {e}")
        return []
