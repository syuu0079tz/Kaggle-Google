"""Command line interface for CareCompass Agent."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .orchestrator import run_agent


def _render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# CareCompass Plan",
        "",
        f"Needs: {', '.join(result['needs'])}",
        f"Urgency: {result['urgency']}",
        "",
        "## Recommendations",
    ]
    for index, item in enumerate(result["recommendations"], start=1):
        lines.extend(
            [
                f"{index}. {item['name']} ({item['category']})",
                f"   - Why: score {item['score']} for the detected needs",
                f"   - Contact: {item['contact']}",
                f"   - Official URL: {item['url']}",
                f"   - Hours: {item['hours']}",
                f"   - Safety note: {item['safety_notes']}",
            ]
        )
    lines.extend(["", "## Next Steps"])
    for step in result["next_steps"]:
        lines.append(f"- {step}")
    lines.extend(["", "## Safety"])
    for notice in result["safety"]["notices"]:
        lines.append(f"- {notice}")
    lines.extend(["", "## Trace"])
    for trace in result["agent_trace"]:
        lines.append(f"- {trace['agent']}: {trace['action']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the CareCompass support navigator.")
    parser.add_argument("request", nargs="*", help="User support request. Reads stdin if omitted.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    user_text = " ".join(args.request).strip() or sys.stdin.read().strip()
    if not user_text:
        parser.error("Provide a request or pipe text on stdin.")

    result = run_agent(user_text)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(_render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
