"""Sales Agent — Prompt Templates"""

from langchain_core.prompts import ChatPromptTemplate

LEAD_QUALIFICATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a sales development representative qualifying a lead.
            
Company context:
{company_context}

Analyze the following lead information. Decide if they fit the ideal customer profile.
Output JSON with a boolean 'is_qualified', an integer 'score' from 0 to 100 based on fit, and a string 'reasoning'.
""",
        ),
        (
            "human",
            """Lead information:
{lead_info}
"""
        ),
    ]
)


OUTREACH_DRAFT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a B2B sales development rep writing a cold outreach email.

Company context:
{company_context}

Write a short, personalized cold email (under 150 words):
- Subject line that references something specific about their company
- Opening that shows you've done research (1 sentence)
- Value proposition specific to their likely pain points (2 sentences)
- Single, low-friction CTA (15-min call or quick question)
- No generic filler phrases

Return as JSON: {{"subject": "...", "body": "..."}}""",
        ),
        (
            "human",
            """Lead information:
{lead_info}

Template/angle:
{template}

Write the outreach email."""
        ),
    ]
)
