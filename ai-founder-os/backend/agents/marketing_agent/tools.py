"""
Marketing Agent — Tools

Wraps MCP clients into LangChain-compatible tools.
All tools that cause side effects (send_email) are gated by the approval system.
"""

from __future__ import annotations

from langchain_core.tools import tool

from mcp_clients.trends_client import search_google_trends
from mcp_clients.gmail_client import send_gmail
from guardrails.approval_gate import requires_approval


@tool
async def search_trends(query: str) -> str:
    """
    Search Google Trends for a topic and return top related queries and interest over time.
    
    Args:
        query: The search topic or keyword
    """
    results = await search_google_trends(query)
    if not results:
        return f"No trend data found for '{query}'"

    lines = [f"Trend data for '{query}':"]
    for item in results.get("rising", [])[:5]:
        lines.append(f"  Rising: {item['query']} (+{item.get('value', '?')}%)")
    for item in results.get("top", [])[:5]:
        lines.append(f"  Top: {item['query']} (score: {item.get('value', '?')})")
    return "\n".join(lines)


@tool
async def draft_content(topic: str, format: str = "linkedin_post") -> str:
    """
    Draft marketing content for a given topic and format.
    
    Args:
        topic: The subject or angle for the content
        format: One of 'linkedin_post', 'tweet', 'blog_outline', 'email_newsletter'
    """
    from langchain_openai import ChatOpenAI
    from agents.marketing_agent.prompts import CONTENT_DRAFT_PROMPT
    from memory.long_term import get_company_profile

    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    chain = CONTENT_DRAFT_PROMPT | llm

    company_context = await get_company_profile()

    response = await chain.ainvoke(
        {
            "topic": topic,
            "format": format,
            "tone": "professional but approachable",
            "audience": "startup founders and operators",
            "company_context": company_context,
        }
    )
    return response.content


@tool
@requires_approval(tool_name="send_email", description="Send a marketing email")
async def send_marketing_email(to: str, subject: str, body: str) -> str:
    """
    Send a marketing email. REQUIRES HUMAN APPROVAL before execution.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body (plain text or HTML)
    """
    result = await send_gmail(to=to, subject=subject, body=body)
    return f"Email sent to {to}: {result}"


# Tool list exposed to the agent
MARKETING_TOOLS = [search_trends, draft_content, send_marketing_email]
