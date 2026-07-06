"""Local evaluation harness for the capstone project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .orchestrator import run_agent


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = PROJECT_ROOT / "evals" / "cases.json"


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    result = run_agent(case["request"])
    checks: dict[str, bool] = {}

    expected_tags = set(case.get("expected_needs", []))
    checks["expected_needs"] = expected_tags.issubset(set(result["needs"]))
    checks["minimum_recommendations"] = len(result["recommendations"]) >= case.get("min_recommendations", 1)
    checks["human_review"] = result["safety"]["requires_human_review"] == case.get(
        "requires_human_review", False
    )
    forbidden_text = case.get("forbidden_text", "")
    checks["pii_not_in_trace"] = (
        True
        if not forbidden_text
        else forbidden_text not in json.dumps(result["agent_trace"], ensure_ascii=False)
    )
    checks["all_tools_allowlisted"] = set(result["tool_allowlist"]) == {
        "get_resource",
        "safety_check",
        "search_resources",
    }

    passed = all(checks.values())
    return {"id": case["id"], "passed": passed, "checks": checks, "result": result}


def run_evaluations(path: Path | str = DEFAULT_CASES) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        cases = json.load(handle)["cases"]
    results = [evaluate_case(case) for case in cases]
    passed = sum(1 for item in results if item["passed"])
    return {"passed": passed, "total": len(results), "results": results}
