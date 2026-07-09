"""
Evals — Run Evaluation Suite

Runs hand-built test cases against each agent and writes results to evals/results/.
Uses a simple assertion-based scorer (LLM-as-judge is planned for v0.2).

Usage:
    python -m evals.run_evals --agent marketing
    python -m evals.run_evals --agent all
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from agents.marketing_agent import run_marketing_agent
from agents.sales_agent import run_sales_agent
from agents.operations_agent import run_operations_agent

RESULTS_DIR = Path(__file__).parent / "results"
TEST_CASES_DIR = Path(__file__).parent / "test_cases"

AGENT_MAP = {
    "marketing": (run_marketing_agent, "marketing_cases.json"),
    "sales": (run_sales_agent, "sales_cases.json"),
    "operations": (run_operations_agent, "operations_cases.json"),
}


async def run_single_eval(
    case: dict[str, Any],
    agent_fn,
    run_id: str,
) -> dict[str, Any]:
    """Run a single eval case and return the result."""
    result = {
        "case_id": case["id"],
        "description": case["description"],
        "passed": False,
        "output": "",
        "errors": [],
        "assertions": [],
    }

    try:
        output = await agent_fn(
            tasks=case["input"]["tasks"],
            run_id=run_id,
        )
        result["output"] = output.get("output", "")

        # Run assertions
        expected = case.get("expected", {})
        assertions = []

        if "output_word_count_max" in expected:
            word_count = len(result["output"].split())
            passed = word_count <= expected["output_word_count_max"]
            assertions.append({
                "name": "output_word_count_max",
                "passed": passed,
                "detail": f"Word count: {word_count} (max: {expected['output_word_count_max']})",
            })

        if "output_word_count_min" in expected:
            word_count = len(result["output"].split())
            passed = word_count >= expected["output_word_count_min"]
            assertions.append({
                "name": "output_word_count_min",
                "passed": passed,
                "detail": f"Word count: {word_count} (min: {expected['output_word_count_min']})",
            })

        if "output_must_mention" in expected:
            for term in expected["output_must_mention"]:
                passed = term.lower() in result["output"].lower()
                assertions.append({
                    "name": f"must_mention:{term}",
                    "passed": passed,
                    "detail": f"'{term}' found: {passed}",
                })

        if "must_not_crash" in expected and expected["must_not_crash"]:
            assertions.append({
                "name": "must_not_crash",
                "passed": True,
                "detail": "Agent completed without exception",
            })

        result["assertions"] = assertions
        result["passed"] = all(a["passed"] for a in assertions)

    except Exception as e:
        # Check if this was an expected failure (e.g., ApprovalPendingError)
        from guardrails.approval_gate import ApprovalPendingError

        if isinstance(e, ApprovalPendingError) and case.get("expected", {}).get("must_raise_approval_pending"):
            result["passed"] = True
            result["assertions"].append({
                "name": "must_raise_approval_pending",
                "passed": True,
                "detail": f"ApprovalPendingError raised as expected: {e.approval_id}",
            })
        else:
            result["errors"].append(str(e))

    return result


async def run_agent_evals(agent_name: str) -> dict[str, Any]:
    """Run all eval cases for an agent and return a results summary."""
    agent_fn, cases_file = AGENT_MAP[agent_name]
    cases_path = TEST_CASES_DIR / cases_file

    with open(cases_path) as f:
        cases = json.load(f)

    results = []
    run_id = f"eval_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print(f"\n{'='*60}")
    print(f"Running {len(cases)} eval cases for {agent_name} agent")
    print(f"{'='*60}")

    for case in cases:
        print(f"\n  [{case['id']}] {case['description']}")
        result = await run_single_eval(case, agent_fn, run_id)
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        print(f"  {status}")
        for assertion in result["assertions"]:
            icon = "  ✓" if assertion["passed"] else "  ✗"
            print(f"    {icon} {assertion['name']}: {assertion['detail']}")
        if result["errors"]:
            for err in result["errors"]:
                print(f"    ✗ ERROR: {err}")
        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    summary = {
        "agent": agent_name,
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "total": total,
        "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%",
        "results": results,
    }

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{total} passed ({summary['pass_rate']})")
    print(f"{'='*60}\n")

    # Write results to file
    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / f"{run_id}.json"
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Results written to {output_path}")

    return summary


async def main(agent: str = "all"):
    agents = list(AGENT_MAP.keys()) if agent == "all" else [agent]
    all_results = []
    for a in agents:
        result = await run_agent_evals(a)
        all_results.append(result)
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI Founder OS evals")
    parser.add_argument(
        "--agent",
        choices=["marketing", "sales", "operations", "all"],
        default="all",
        help="Which agent to evaluate",
    )
    args = parser.parse_args()
    asyncio.run(main(agent=args.agent))
