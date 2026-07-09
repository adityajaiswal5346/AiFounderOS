"""
API Route — /api/roadmap

Serves the current roadmap state for the frontend roadmap editor.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import RoadmapResponse, RoadmapSection, RoadmapItem

router = APIRouter()

# Static roadmap definition — in v0.2 this would come from a DB-backed editor
ROADMAP_DATA: list[dict] = [
    {
        "section": "Agents",
        "items": [
            {"title": "CEO Agent (planner, arbitration, digest)", "status": "built"},
            {"title": "Marketing Agent (ReAct, trend search, content draft)", "status": "built"},
            {"title": "Sales Agent (pipeline, outreach)", "status": "built"},
            {"title": "Operations Agent (Notion, docs)", "status": "built"},
            {"title": "Finance Agent", "status": "stub", "notes": "Requires QuickBooks/Xero integration"},
            {"title": "Customer Success Agent", "status": "stub", "notes": "Requires HubSpot + Intercom"},
            {"title": "R&D Agent", "status": "stub", "notes": "Requires GitHub + arXiv APIs"},
        ],
    },
    {
        "section": "Infrastructure",
        "items": [
            {"title": "LangGraph orchestration", "status": "built"},
            {"title": "Approval gate (tool-layer)", "status": "built"},
            {"title": "Short-term and long-term memory", "status": "built"},
            {"title": "pgvector RAG retrieval", "status": "built"},
            {"title": "Langfuse tracing", "status": "built"},
            {"title": "FastAPI backend", "status": "built"},
            {"title": "Next.js frontend", "status": "built"},
        ],
    },
    {
        "section": "MCP Clients",
        "items": [
            {"title": "Gmail", "status": "built"},
            {"title": "Google Sheets", "status": "built"},
            {"title": "Notion", "status": "built"},
            {"title": "Slack", "status": "built"},
            {"title": "Google Trends", "status": "built"},
        ],
    },
    {
        "section": "Planned (v0.2)",
        "items": [
            {"title": "Finance Agent implementation", "status": "planned"},
            {"title": "Customer Success Agent implementation", "status": "planned"},
            {"title": "R&D Agent implementation", "status": "planned"},
            {"title": "LLM-as-judge eval scoring", "status": "planned"},
            {"title": "Multi-tenant support", "status": "planned"},
            {"title": "Full frontend interactivity", "status": "planned"},
        ],
    },
]


@router.get("/", response_model=RoadmapResponse)
async def get_roadmap():
    """Get the current project roadmap."""
    sections = [
        RoadmapSection(
            section=s["section"],
            items=[RoadmapItem(**item) for item in s["items"]],
        )
        for s in ROADMAP_DATA
    ]
    return RoadmapResponse(sections=sections, last_updated="2026-07-10")
