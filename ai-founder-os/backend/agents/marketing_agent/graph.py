"""
Marketing Agent — LangGraph Subgraph

Phase 6 V1:
Marketing Task -> Trend Research -> Opportunity Analysis -> Content Generation -> LinkedIn Draft -> Approval Gate -> Storage
"""

import json
from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db.models import Task
from llm.provider import get_model
from guardrails.approval_gate import check_and_gate, ApprovalPending
from mcp_clients.trends_client import search_google_trends
from memory.long_term import get_company_profile
from memory.retrieval import retrieve_context
from .prompts import OPPORTUNITY_ANALYSIS_PROMPT, LINKEDIN_DRAFT_PROMPT


class MarketingState(TypedDict):
    db: AsyncSession
    task: Task
    status: str
    summary: str
    
    # Workflow specific state
    research_results: str
    opportunity: dict[str, str]
    draft_content: str
    retrieved_context: str


class Opportunity(BaseModel):
    topic: str = Field(description="The primary topic")
    audience: str = Field(description="The target audience")
    angle: str = Field(description="The marketing angle")
    format: str = Field(description="The format (e.g. LinkedIn Post)")
    cta: str = Field(description="The call to action")


async def retrieve_node(state: MarketingState) -> dict:
    """Retrieve semantic context related to the task."""
    try:
        results = await retrieve_context(state["task"].description, top_k=3)
        if results:
            formatted = "\n\n".join([r["content"] for r in results])
            return {"retrieved_context": formatted}
    except Exception as e:
        # If retrieval fails (e.g. missing API key, no DB), gracefully return empty
        pass
    
    return {"retrieved_context": ""}


async def research_node(state: MarketingState) -> dict:
    """Research relevant trends based on the task description."""
    # Simple extraction of keyword from task description for V1
    query = state["task"].description or "AI startups"
    
    # In a real scenario, we might use an LLM to extract the best search query.
    # For V1, we just take a chunk of the task description or a default.
    words = query.split()
    search_term = " ".join(words[:4]) if len(words) > 4 else query
    
    results = await search_google_trends(search_term)
    return {"research_results": str(results)}


async def analysis_node(state: MarketingState) -> dict:
    """Analyze research and determine a content opportunity."""
    company_context = await get_company_profile()
    model = get_model(temperature=0.4).with_structured_output(Opportunity)
    
    response = await model.ainvoke(
        OPPORTUNITY_ANALYSIS_PROMPT.format_messages(
            task=state["task"].description,
            research=state["research_results"],
            company_context=company_context,
            retrieved_context=state.get("retrieved_context", "")
        )
    )
    
    return {"opportunity": response.model_dump()}


async def draft_node(state: MarketingState) -> dict:
    """Generate a LinkedIn draft based on the opportunity."""
    company_context = await get_company_profile()
    model = get_model(temperature=0.7)
    
    response = await model.ainvoke(
        LINKEDIN_DRAFT_PROMPT.format_messages(
            topic=state["opportunity"]["topic"],
            angle=state["opportunity"]["angle"],
            audience=state["opportunity"]["audience"],
            cta=state["opportunity"]["cta"],
            company_context=company_context,
            retrieved_context=state.get("retrieved_context", "")
        )
    )
    
    return {"draft_content": response.content}


async def approval_node(state: MarketingState) -> dict:
    """Halt for founder approval before publishing."""
    try:
        # We use a placeholder tool name 'publish_post' which requires approval
        await check_and_gate(
            state["db"], 
            state["task"].id, 
            "publish_post", 
            {"platform": "linkedin", "content": state["draft_content"]}
        )
        return {"status": "approved"}
    except ApprovalPending as e:
        return {
            "status": "awaiting_approval",
            "summary": f"Blocked: {e.tool_name} requires approval (ID: {e.approval_id})"
        }


async def publish_node(state: MarketingState) -> dict:
    """Store the approved content (fallback for unavailable LinkedIn API)."""
    # Since LinkedIn publishing is UNAVAILABLE, we just store it as the outcome summary
    summary = f"Content approved and stored for publishing.\n\nDraft:\n{state['draft_content']}"
    return {"status": "completed", "summary": summary}


def route_after_approval(state: MarketingState) -> str:
    if state["status"] == "awaiting_approval":
        return END
    return "publish_node"


def build_marketing_graph() -> StateGraph:
    """Compile the Marketing state graph."""
    graph = StateGraph(MarketingState)

    graph.add_node("retrieve_node", retrieve_node)
    graph.add_node("research_node", research_node)
    graph.add_node("analysis_node", analysis_node)
    graph.add_node("draft_node", draft_node)
    graph.add_node("approval_node", approval_node)
    graph.add_node("publish_node", publish_node)

    graph.set_entry_point("retrieve_node")
    graph.add_edge("retrieve_node", "research_node")
    graph.add_edge("research_node", "analysis_node")
    graph.add_edge("analysis_node", "draft_node")
    graph.add_edge("draft_node", "approval_node")
    graph.add_conditional_edges("approval_node", route_after_approval)
    graph.add_edge("publish_node", END)

    return graph.compile()
