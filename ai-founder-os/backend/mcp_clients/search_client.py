"""
MCP Client — Web Search

Search the web using SerpAPI.
Used by the Sales Agent for prospect/company research.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

SERPAPI_BASE_URL = "https://serpapi.com/search"


async def search_google(
    query: str,
    num_results: int = 3,
) -> str:
    """
    Search Google for a query via SerpAPI.

    Args:
        query: Search term
        num_results: Number of organic results to return

    Returns:
        Formatted string of search results
    """
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        logger.warning("SERPAPI_KEY not set — returning mock search data")
        return _mock_search(query)

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num_results,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(SERPAPI_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            organic = data.get("organic_results", [])
            results = []
            for item in organic[:num_results]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                results.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}\n")
                
            return "\n".join(results) if results else "No results found."
        except httpx.HTTPError as e:
            logger.error(f"SerpAPI request failed for query '{query}': {e}")
            raise


def _mock_search(query: str) -> str:
    """Return mock search data when API key is not available (for local dev/testing)."""
    return f"""Title: About {query}
Snippet: {query} is a leading company in its industry, recently launching new AI products.
Link: https://example.com/about

Title: Recent News: {query}
Snippet: {query} announces record-breaking Q3 earnings and expansion into Europe.
Link: https://example.com/news
"""
