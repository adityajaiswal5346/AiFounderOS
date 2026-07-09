"""
Observability — Langfuse Tracing

Wraps LLM calls, tool calls, and agent runs with Langfuse traces.
All trace IDs are stored alongside task and outcome records for debugging.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Langfuse setup
try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context

    LANGFUSE_ENABLED = all(
        [
            os.environ.get("LANGFUSE_PUBLIC_KEY"),
            os.environ.get("LANGFUSE_SECRET_KEY"),
        ]
    )

    if LANGFUSE_ENABLED:
        langfuse_client = Langfuse(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        logger.info("Langfuse tracing enabled")
    else:
        langfuse_client = None
        logger.warning("Langfuse credentials not set — tracing disabled")

except ImportError:
    LANGFUSE_ENABLED = False
    langfuse_client = None
    logger.warning("Langfuse not installed — tracing disabled")


def get_tracer():
    """
    Get the Langfuse tracer instance (or a no-op stub if tracing is disabled).

    Returns:
        Langfuse client or NoOpTracer
    """
    if LANGFUSE_ENABLED and langfuse_client:
        return langfuse_client
    return NoOpTracer()


class NoOpTracer:
    """
    No-op tracer stub for when Langfuse is not available.
    Implements the minimal context manager interface.
    """

    def start_as_current_span(self, name: str, **kwargs):
        return NoOpSpan()


class NoOpSpan:
    """No-op span context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# ── Decorators for manual instrumentation ──────────────────────────────────────

def trace_agent_run(agent_name: str):
    """
    Decorator to trace an entire agent run as a Langfuse trace.

    Usage:
        @trace_agent_run("marketing")
        async def run_marketing_agent(tasks, run_id):
            ...
    """
    if not LANGFUSE_ENABLED:
        return lambda fn: fn  # no-op if tracing is disabled

    def decorator(fn):
        return observe(name=f"{agent_name}_agent_run")(fn)

    return decorator


def trace_tool_call(tool_name: str):
    """
    Decorator to trace a tool invocation as a Langfuse span.

    Usage:
        @trace_tool_call("search_trends")
        async def search_trends(query: str):
            ...
    """
    if not LANGFUSE_ENABLED:
        return lambda fn: fn

    def decorator(fn):
        return observe(name=f"tool.{tool_name}")(fn)

    return decorator


# ── Context helpers ────────────────────────────────────────────────────────────

def get_current_trace_id() -> str | None:
    """Get the current Langfuse trace ID, if available."""
    if not LANGFUSE_ENABLED:
        return None
    try:
        return langfuse_context.get_current_trace_id()
    except Exception:
        return None
