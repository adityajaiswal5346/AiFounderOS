"""
CEO Agent — Daily Digest Synthesis

Collects outputs from all specialist agents and produces a founder-readable
daily digest. Includes:
- Summary of what each agent accomplished
- Key decisions made (and why)
- Pending approvals
- Blockers or failures
- Recommended founder actions
"""

from __future__ import annotations

from datetime import date
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel

from llm.provider import get_model
from observability.tracing import observe

DIGEST_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are synthesizing a daily digest for a founder. Be concise and direct.
            
Date: {today}

Marketing Agent Output:
{marketing_output}

Sales Agent Output:
{sales_output}

Operations Agent Output:
{operations_output}

Pending Approvals:
{pending_approvals}

Conflicts Detected:
{conflicts}

Conflict Resolutions / Recommendations:
{resolutions}

Write a founder digest with these sections:
1. **Today's Wins** (bullet points, max 5)
2. **Needs Your Attention** (approvals or blockers requiring action)
3. **Key Numbers** (metrics moved today, if any)
4. **Conflicts & Resolutions** (summarize any detected conflicts and the arbitration decisions)
5. **Tomorrow's Focus** (1-2 sentences)

Keep the total digest under 300 words.""",
        ),
        ("human", "Synthesize the daily digest."),
    ]
)


@observe(name="ceo_synthesize_digest")
async def synthesize_digest(
    agent_outputs: dict[str, Any],
    pending_approvals: list[dict[str, Any]],
    conflicts: list[dict[str, Any]] | None = None,
    resolutions: list[dict[str, Any]] | None = None,
    llm: BaseChatModel | None = None,
) -> dict[str, str]:
    """
    Synthesize a daily digest from all agent outputs.

    Args:
        agent_outputs: dict with keys 'marketing', 'sales', 'operations'
        pending_approvals: list of approval requests awaiting founder action
        conflicts: optional list of detected conflicts
        resolutions: optional list of arbitration resolutions

    Returns:
        dict with 'markdown' (formatted digest) and 'raw' (plain text)
    """
    if llm is None:
        llm = get_model(temperature=0.3)

    chain = DIGEST_PROMPT | llm

    response = await chain.ainvoke(
        {
            "today": date.today().isoformat(),
            "marketing_output": agent_outputs.get("marketing", "No output"),
            "sales_output": agent_outputs.get("sales", "No output"),
            "operations_output": agent_outputs.get("operations", "No output"),
            "pending_approvals": (
                "\n".join(
                    f"- [{a['tool']}] {a['description']}" for a in pending_approvals
                )
                if pending_approvals
                else "None"
            ),
            "conflicts": (
                "\n".join(str(c) for c in conflicts) if conflicts else "None"
            ),
            "resolutions": (
                "\n".join(str(r) for r in resolutions) if resolutions else "None"
            ),
        }
    )

    return {
        "markdown": response.content,
        "raw": response.content,
        "date": date.today().isoformat(),
        "pending_approval_count": len(pending_approvals),
    }
