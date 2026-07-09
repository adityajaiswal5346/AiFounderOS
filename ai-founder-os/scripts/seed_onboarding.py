"""
Script — Seed Onboarding Memory

Seeds the long-term memory database with a new founder's company profile.
Run this once before the first daily cycle.

Usage:
    python scripts/seed_onboarding.py
    python scripts/seed_onboarding.py --config my_company.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from memory.retrieval import index_document
from memory.long_term import save_memory


# Default onboarding template (can be overridden with --config)
DEFAULT_PROFILE = {
    "company_profile": """
Company: [Your Company Name]
Stage: Pre-seed / Seed
Industry: B2B SaaS
Mission: [Your mission statement]

Current Goals:
- Get to 10 paying customers
- Validate core value proposition
- Build the founding team to 3 people

Team:
- [Founder Name] - CEO / Technical Founder

Target Customer:
- [ICP description]

Key Metrics (as of today):
- MRR: $0
- Customers: 0
- Waitlist: 50

Competitors:
- [Competitor 1]
- [Competitor 2]

Current Priorities:
1. Customer discovery (talk to 20 potential customers this month)
2. MVP feature: [core feature]
3. First paid customer

Budget:
- Monthly burn: ~$X,XXX
- Runway: ~X months
""".strip(),

    "company_decisions": """
Key decisions made so far:
- Chose B2B over B2C (higher LTV, clearer buyers)
- Starting with [specific vertical] before expanding
- No-code/low-code stack for fast iteration
""".strip(),

    "sales_pipeline_context": """
Sales pipeline is tracked in Google Sheets.
Columns: ID, Company, Contact, Email, Stage, Notes, Last Contact

Lead stages:
- identified: Found in the wild
- contacted: First outreach sent  
- responded: They replied
- qualified: Had a discovery call
- proposal: Sent pricing/demo
- closed_won: Paying customer
- closed_lost: Not a fit
""".strip(),

    "marketing_context": """
Marketing channels:
- LinkedIn (primary B2B channel)
- Cold email (outreach to warm leads)
- Content marketing (starting a newsletter)

Brand voice: Direct, honest, slightly technical. No buzzwords.
Tone: Like a smart founder talking to another founder.
""".strip(),

    "operations_context": """
Tools we use:
- Notion: Task management and documentation
- Slack: Team communication (solo founder: using for bot notifications)
- Google Workspace: Email, Sheets, Docs

Meeting cadence:
- Weekly: Review pipeline and tasks
- Monthly: Strategy review
""".strip(),
}


async def seed_memory(profile: dict) -> None:
    """Write all profile entries to long-term memory with embeddings."""
    print("Seeding long-term memory...")

    for key, value in profile.items():
        print(f"  ↳ Indexing: {key}")
        await index_document(key=key, content=value)

    print(f"\n✓ Seeded {len(profile)} memory entries")
    print("\nNext step: run the first daily cycle:")
    print("  python scripts/run_daily_cycle.py")


async def main(config_path: str | None = None):
    if config_path:
        print(f"Loading company profile from: {config_path}")
        with open(config_path) as f:
            profile = json.load(f)
    else:
        print("Using default onboarding template.")
        print("Tip: Copy and edit the profile in this script, or pass --config your_profile.json\n")
        profile = DEFAULT_PROFILE

    await seed_memory(profile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed AI Founder OS onboarding memory")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to a JSON file with company profile data",
        default=None,
    )
    args = parser.parse_args()
    asyncio.run(main(config_path=args.config))
