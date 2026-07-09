"""
Sales Agent — Tools

Wraps MCP clients for lead management and outreach.
Email sends require human approval via the approval gate.
"""

from __future__ import annotations

from langchain_core.tools import tool

from mcp_clients.sheets_client import read_sheet, update_sheet_row
from mcp_clients.gmail_client import send_gmail
from guardrails.approval_gate import requires_approval


@tool
async def read_leads_sheet() -> str:
    """
    Read the current leads pipeline from Google Sheets.
    Returns rows as a formatted table string.
    """
    rows = await read_sheet(sheet_name="Leads")
    if not rows:
        return "No leads found in pipeline."

    # Format as readable table
    lines = ["Lead Pipeline:"]
    headers = rows[0] if rows else []
    for row in rows[1:]:
        lead = dict(zip(headers, row))
        lines.append(
            f"  [{lead.get('ID', '?')}] {lead.get('Company', '?')} — "
            f"{lead.get('Contact', '?')} — Status: {lead.get('Status', '?')}"
        )
    return "\n".join(lines)


@tool
async def update_lead_status(row_id: str, status: str, notes: str = "") -> str:
    """
    Update a lead's status in the Google Sheets pipeline.

    Args:
        row_id: The row identifier for the lead
        status: New status (e.g., 'contacted', 'qualified', 'closed_won', 'closed_lost')
        notes: Optional notes about the status change
    """
    await update_sheet_row(
        sheet_name="Leads",
        row_id=row_id,
        updates={"Status": status, "Notes": notes},
    )
    return f"Updated lead {row_id} to status '{status}'"


@tool
async def draft_outreach_email(lead_info: str, template: str = "cold_intro") -> str:
    """
    Draft a personalized outreach email for a lead.

    Args:
        lead_info: JSON string or description of the lead (company, name, role, context)
        template: Template type — 'cold_intro', 'follow_up', 're_engage'
    """
    from langchain_openai import ChatOpenAI
    from agents.sales_agent.prompts import OUTREACH_DRAFT_PROMPT
    from memory.long_term import get_company_profile

    llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
    chain = OUTREACH_DRAFT_PROMPT | llm

    company_context = await get_company_profile()
    response = await chain.ainvoke(
        {
            "lead_info": lead_info,
            "template": template,
            "company_context": company_context,
        }
    )
    return response.content


@tool
@requires_approval(tool_name="send_email", description="Send a sales outreach email")
async def send_outreach_email(to: str, subject: str, body: str) -> str:
    """
    Send an outreach email to a lead. REQUIRES HUMAN APPROVAL before execution.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body text
    """
    result = await send_gmail(to=to, subject=subject, body=body)
    return f"Email sent to {to}: {result}"


# Tool list exposed to the agent
SALES_TOOLS = [read_leads_sheet, update_lead_status, draft_outreach_email, send_outreach_email]
