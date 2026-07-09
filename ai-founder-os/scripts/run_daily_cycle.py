"""
Script — Manual Daily Cycle Trigger

Runs the full daily agent cycle manually. Use this for demos or testing
without waiting for the scheduler's 7AM cron.

Usage:
    python scripts/run_daily_cycle.py
    python scripts/run_daily_cycle.py --run-id my_test_run
    python scripts/run_daily_cycle.py --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from orchestration.scheduler import run_daily_cycle


async def main(run_id: str | None = None, verbose: bool = False) -> None:
    if run_id is None:
        run_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    print(f"Starting daily cycle...")
    print(f"Run ID: {run_id}")
    print(f"Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("─" * 50)

    start = datetime.now()
    final_state = await run_daily_cycle(run_id=run_id)
    elapsed = (datetime.now() - start).total_seconds()

    print("\n" + "─" * 50)
    print(f"✓ Cycle complete in {elapsed:.1f}s")

    # Show errors if any
    errors = final_state.get("errors", [])
    if errors:
        print(f"\n⚠ {len(errors)} error(s):")
        for err in errors:
            print(f"  • {err}")

    # Show digest summary
    digest = final_state.get("digest", {})
    if digest:
        print(f"\n📋 Digest preview:")
        preview = digest.get("markdown", "")[:500]
        print(preview + ("..." if len(digest.get("markdown", "")) > 500 else ""))

    # Show pending approvals
    pending = final_state.get("pending_approvals", [])
    if pending:
        print(f"\n⚠ {len(pending)} pending approval(s) — review at http://localhost:3000/approvals")

    if verbose:
        print(f"\n📊 Full state:")
        # Redact embeddings and large fields for display
        display_state = {
            k: v for k, v in final_state.items()
            if k != "digest" and not isinstance(v, bytes)
        }
        print(json.dumps(display_state, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manually trigger AI Founder OS daily cycle")
    parser.add_argument("--run-id", type=str, default=None, help="Custom run ID")
    parser.add_argument("--verbose", action="store_true", help="Print full state output")
    args = parser.parse_args()
    asyncio.run(main(run_id=args.run_id, verbose=args.verbose))
