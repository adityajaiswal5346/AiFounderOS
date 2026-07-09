"""
MCP Client — Google Trends

Search Google Trends for topic interest data using SerpAPI.
Used by the Marketing Agent for content research.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SERPAPI_BASE_URL = "https://serpapi.com/search"


async def search_google_trends(
    query: str,
    geo: str = "US",
    timeframe: str = "today 3-m",
) -> dict[str, Any]:
    """
    Search Google Trends for a query via SerpAPI.

    Args:
        query: Search term or topic
        geo: Geographic location code (default: US)
        timeframe: Time range (default: last 3 months)

    Returns:
        Dict with 'rising' and 'top' related queries, and 'interest_over_time'
    """
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        logger.warning("SERPAPI_KEY not set — returning mock trend data")
        return _mock_trends(query)

    params = {
        "engine": "google_trends",
        "q": query,
        "geo": geo,
        "date": timeframe,
        "api_key": api_key,
        "data_type": "RELATED_QUERIES",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(SERPAPI_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            related = data.get("related_queries", {})
            return {
                "query": query,
                "rising": related.get("rising", []),
                "top": related.get("top", []),
                "interest_over_time": data.get("interest_over_time", {}).get("timeline_data", []),
            }
        except httpx.HTTPError as e:
            logger.error(f"SerpAPI request failed for query '{query}': {e}")
            raise


def _mock_trends(query: str) -> dict[str, Any]:
    """Return mock trend data when API key is not available (for local dev/testing)."""
    return {
        "query": query,
        "rising": [
            {"query": f"{query} tools", "value": 250},
            {"query": f"{query} examples", "value": 180},
            {"query": f"best {query}", "value": 120},
        ],
        "top": [
            {"query": f"what is {query}", "value": 100},
            {"query": f"{query} tutorial", "value": 85},
            {"query": f"{query} vs alternatives", "value": 70},
        ],
        "interest_over_time": [],
        "_mock": True,
    }
