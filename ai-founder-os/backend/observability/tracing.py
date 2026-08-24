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
    
    def observe(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator


def get_langfuse_callback():
    """
    Get the Langfuse Langchain callback handler if tracing is enabled.
    Can be passed into the config of any Langchain/Langgraph invocation.
    
    Returns:
        LangfuseCallbackHandler or None
    """
    if LANGFUSE_ENABLED:
        try:
            from langfuse.callback import CallbackHandler
            return CallbackHandler(
                public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
                secret_key=os.environ["LANGFUSE_SECRET_KEY"],
                host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
        except ImportError:
            return None
    return None

# Keep get_current_trace_id helper
def get_current_trace_id() -> str | None:
    """Get the current Langfuse trace ID, if available."""
    if not LANGFUSE_ENABLED:
        return None
    try:
        from langfuse.decorators import langfuse_context
        return langfuse_context.get_current_trace_id()
    except Exception:
        return None
