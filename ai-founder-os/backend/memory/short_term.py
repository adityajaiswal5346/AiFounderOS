"""
Memory — Short-Term Context

Stores per-run context in memory (backed by a dict keyed by run_id).
This is the current-day working context passed between graph nodes.
Cleared at the end of each daily run.
"""

from __future__ import annotations

from typing import Any

# In-memory store: run_id → context dict
_store: dict[str, dict[str, Any]] = {}


async def get_current_context(run_id: str) -> dict[str, Any]:
    """
    Get the current short-term context for a run.

    Args:
        run_id: The daily run identifier

    Returns:
        Context dict (empty if no context set for this run)
    """
    return _store.get(run_id, {})


async def set_context(run_id: str, key: str, value: Any) -> None:
    """
    Set a key-value pair in the short-term context for a run.

    Args:
        run_id: The daily run identifier
        key: Context key
        value: Context value (must be JSON-serializable)
    """
    if run_id not in _store:
        _store[run_id] = {}
    _store[run_id][key] = value


async def update_context(run_id: str, updates: dict[str, Any]) -> None:
    """
    Merge a dict of updates into the short-term context for a run.

    Args:
        run_id: The daily run identifier
        updates: Dict of key-value pairs to merge
    """
    if run_id not in _store:
        _store[run_id] = {}
    _store[run_id].update(updates)


async def clear_context(run_id: str) -> None:
    """
    Clear the short-term context for a completed run.

    Args:
        run_id: The daily run identifier
    """
    _store.pop(run_id, None)
