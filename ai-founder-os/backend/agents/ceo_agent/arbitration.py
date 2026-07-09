"""
CEO Agent — Arbitration

Resolves conflicts between specialist agents:
- Resource contention (e.g., two agents want to email the same contact)
- Priority conflicts (e.g., Marketing and Sales both want top CEO attention)
- Budget conflicts (spending limits exceeded across agents)
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

ARBITRATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a CEO arbitrating a conflict between your AI department heads.
            
Conflict details:
{conflict}

Agent A position:
{agent_a}

Agent B position:
{agent_b}

Resolve this conflict clearly. State:
1. Your decision
2. Your reasoning (1-2 sentences)
3. Any conditions or constraints on the winning agent

Respond in JSON:
{{
  "winner": "marketing|sales|operations|neither",
  "decision": "...",
  "reasoning": "...",
  "constraints": "..."
}}""",
        ),
        ("human", "Resolve the conflict."),
    ]
)


async def arbitrate_conflicts(
    conflicts: list[dict[str, Any]],
    llm: ChatOpenAI | None = None,
) -> list[dict[str, Any]]:
    """
    Arbitrate a list of conflicts between agents.

    Args:
        conflicts: List of conflict dicts with keys: description, agent_a, agent_b, positions

    Returns:
        List of resolution dicts
    """
    if not conflicts:
        return []

    if llm is None:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

    chain = ARBITRATION_PROMPT | llm

    resolutions = []
    for conflict in conflicts:
        response = await chain.ainvoke(
            {
                "conflict": conflict.get("description", ""),
                "agent_a": conflict.get("agent_a_position", ""),
                "agent_b": conflict.get("agent_b_position", ""),
            }
        )

        import json

        content = response.content
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        resolution = json.loads(content.strip())
        resolution["conflict_id"] = conflict.get("id")
        resolutions.append(resolution)

    return resolutions
