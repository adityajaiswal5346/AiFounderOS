"""
Sales Agent — LangGraph Subgraph

Phase 6 V1:
Lead Ingestion -> Lead Qualification -> Lead Research -> Personalized Outreach -> Approval Gate -> Send Outreach -> Pipeline Update
"""

import json
from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db.models import Task
from llm.provider import get_model
from guardrails.approval_gate import check_and_gate, ApprovalPending
from mcp_clients.sheets_client import read_sheet, update_sheet_row
from mcp_clients.gmail_client import send_gmail
from memory.long_term import get_company_profile
from mcp_clients.search_client import search_google
from .prompts import LEAD_QUALIFICATION_PROMPT, OUTREACH_DRAFT_PROMPT


class SalesState(TypedDict):
    db: AsyncSession
    task: Task
    status: str
    summary: str
    
    # Workflow specific state
    leads: list[dict[str, Any]]
    current_lead: dict[str, Any]
    qualification: dict[str, Any]
    prospect_research: str
    draft_email: dict[str, str]


class Qualification(BaseModel):
    is_qualified: bool = Field(description="Whether the lead fits the ideal customer profile")
    score: int = Field(description="Lead score from 0 to 100 based on ICP fit")
    reasoning: str = Field(description="Reasoning for the qualification status and score")


class EmailDraft(BaseModel):
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body text")


async def ingest_node(state: SalesState) -> dict:
    """Read new leads from Google Sheets."""
    rows = await read_sheet(sheet_name="Leads")
    if not rows:
        return {"status": "completed", "summary": "No leads found in pipeline."}
    
    headers = rows[0]
    leads = []
    for row in rows[1:]:
        lead = dict(zip(headers, row))
        if lead.get("Status", "").lower() in ["new", ""]:
            leads.append(lead)
            
    if not leads:
        return {"status": "completed", "summary": "No new leads to process."}
        
    return {"leads": leads, "current_lead": leads[0]}


async def qualify_node(state: SalesState) -> dict:
    """Qualify the current lead."""
    company_context = await get_company_profile()
    model = get_model(temperature=0.0).with_structured_output(Qualification)
    
    response = await model.ainvoke(
        LEAD_QUALIFICATION_PROMPT.format_messages(
            lead_info=str(state["current_lead"]),
            company_context=company_context
        )
    )
    
    return {"qualification": response.model_dump()}


async def research_node(state: SalesState) -> dict:
    """Research the prospect's company using web search."""
    company = state["current_lead"].get("Company") or state["current_lead"].get("Email", "")
    query = f"{company} company overview news"
    research_results = await search_google(query)
    return {"prospect_research": research_results}


async def draft_node(state: SalesState) -> dict:
    """Generate a personalized outreach email."""
    company_context = await get_company_profile()
    model = get_model(temperature=0.4).with_structured_output(EmailDraft)
    
    # Combine company profile and prospect research
    enriched_lead_info = f"Lead: {state['current_lead']}\n\nWeb Research on Prospect:\n{state.get('prospect_research', 'None')}"
    
    response = await model.ainvoke(
        OUTREACH_DRAFT_PROMPT.format_messages(
            lead_info=enriched_lead_info,
            template="cold_intro",
            company_context=company_context
        )
    )
    
    return {"draft_email": response.model_dump()}


async def approval_node(state: SalesState) -> dict:
    """Halt for founder approval before sending the email."""
    try:
        await check_and_gate(
            state["db"], 
            state["task"].id, 
            "send_email", 
            {
                "to": state["current_lead"].get("Email", "unknown"),
                "subject": state["draft_email"]["subject"],
                "body": state["draft_email"]["body"]
            }
        )
        return {"status": "approved"}
    except ApprovalPending as e:
        return {
            "status": "awaiting_approval",
            "summary": f"Blocked: {e.tool_name} requires approval (ID: {e.approval_id})"
        }


async def execute_node(state: SalesState) -> dict:
    """Send the email and update the pipeline."""
    lead = state["current_lead"]
    to_email = lead.get("Email")
    
    if not to_email:
        return {"status": "failed", "summary": "Lead has no email address."}
        
    # Send email
    result = await send_gmail(
        to=to_email,
        subject=state["draft_email"]["subject"],
        body=state["draft_email"]["body"]
    )
    
    # Update sheet
    row_id = lead.get("ID")
    if row_id:
        await update_sheet_row(
            sheet_name="Leads",
            row_id=row_id,
            updates={"Status": "Contacted", "Notes": "Outreach sent via Sales Agent."}
        )
        
    summary = f"Email sent to {to_email}. Pipeline updated.\nResult: {result}"
    return {"status": "completed", "summary": summary}


async def skip_node(state: SalesState) -> dict:
    """Handle unqualified leads."""
    lead = state["current_lead"]
    row_id = lead.get("ID")
    if row_id:
        await update_sheet_row(
            sheet_name="Leads",
            row_id=row_id,
            updates={"Status": "Disqualified", "Notes": state["qualification"]["reasoning"]}
        )
        
    summary = f"Lead {lead.get('Company', 'Unknown')} disqualified: {state['qualification']['reasoning']}"
    return {"status": "completed", "summary": summary}


def route_after_ingest(state: SalesState) -> str:
    if state.get("status") == "completed":
        return END
    return "qualify_node"


def route_after_qualify(state: SalesState) -> str:
    if state["qualification"].get("is_qualified"):
        return "research_node"
    return "skip_node"


def route_after_draft(state: SalesState) -> str:
    return "approval_node"


def route_after_approval(state: SalesState) -> str:
    if state["status"] == "awaiting_approval":
        return END
    return "execute_node"


def build_sales_graph() -> StateGraph:
    """Compile the Sales state graph."""
    graph = StateGraph(SalesState)

    graph.add_node("ingest_node", ingest_node)
    graph.add_node("qualify_node", qualify_node)
    graph.add_node("research_node", research_node)
    graph.add_node("draft_node", draft_node)
    graph.add_node("approval_node", approval_node)
    graph.add_node("execute_node", execute_node)
    graph.add_node("skip_node", skip_node)

    graph.set_entry_point("ingest_node")
    graph.add_conditional_edges("ingest_node", route_after_ingest)
    
    graph.add_conditional_edges("qualify_node", route_after_qualify)
    graph.add_edge("research_node", "draft_node")
    graph.add_conditional_edges("draft_node", route_after_draft)
    
    graph.add_conditional_edges("approval_node", route_after_approval)
    
    graph.add_edge("execute_node", END)
    graph.add_edge("skip_node", END)

    return graph.compile()
