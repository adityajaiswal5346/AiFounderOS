"""
Guardrails — Approval Policies

Defines which tool calls require human approval and budget limits.
This is the single source of truth for guardrail configuration.
Policy is loaded from environment variables at startup so it can be
adjusted without code changes.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# ── Tool approval policy ───────────────────────────────────────────────────────

# Default tools that always require approval (can be overridden via env)
DEFAULT_APPROVAL_REQUIRED = {
    "send_email",
    "post_content",
    "update_crm",
    "send_slack_notification",
    "publish_post",
}

# Load override from environment (comma-separated tool names)
_env_approval_tools = os.environ.get("APPROVAL_REQUIRED_ACTIONS", "")
if _env_approval_tools:
    APPROVAL_REQUIRED_TOOLS: set[str] = set(
        t.strip() for t in _env_approval_tools.split(",") if t.strip()
    )
    logger.info(f"Approval tools loaded from env: {APPROVAL_REQUIRED_TOOLS}")
else:
    APPROVAL_REQUIRED_TOOLS = DEFAULT_APPROVAL_REQUIRED


def requires_human_approval(tool_name: str) -> bool:
    """
    Return True if the given tool name requires human approval before execution.

    Args:
        tool_name: The tool identifier (must match what's registered in the policy)

    Returns:
        True if approval is required, False otherwise
    """
    return tool_name in APPROVAL_REQUIRED_TOOLS


# ── Budget limits ──────────────────────────────────────────────────────────────

def get_daily_budget_limit() -> float:
    """
    Get the maximum USD spend allowed per daily run across all LLM + API calls.

    Returns:
        Budget limit in USD (default: $10.00)
    """
    try:
        return float(os.environ.get("DAILY_BUDGET_LIMIT_USD", "10.0"))
    except ValueError:
        logger.warning("Invalid DAILY_BUDGET_LIMIT_USD value, using default $10.00")
        return 10.0


# ── Agent-level restrictions ───────────────────────────────────────────────────

# Map of agent → max number of external API calls per run
# Prevents runaway loops from consuming quota
AGENT_CALL_LIMITS: dict[str, int] = {
    "marketing": 20,
    "sales": 20,
    "operations": 20,
    "ceo": 10,
}


def get_call_limit(agent_name: str) -> int:
    """
    Get the maximum number of tool calls allowed for an agent per run.

    Args:
        agent_name: Agent identifier

    Returns:
        Max call count (default: 20)
    """
    return AGENT_CALL_LIMITS.get(agent_name, 20)
