"""Optional Google ADK entrypoint.

The core repository runs without third-party dependencies. Install
requirements-adk.txt to use this file with Google ADK.
"""

from __future__ import annotations

import os
from typing import Any

from .gemini import DEFAULT_GEMINI_MODEL
from .orchestrator import run_agent


def create_plan(request: str) -> dict[str, Any]:
    """ADK tool wrapper around the deterministic multi-agent workflow."""

    return run_agent(request)


def build_root_agent() -> Any:
    try:
        from google.adk import Agent
    except ImportError as exc:
        raise RuntimeError(
            "Google ADK is not installed. Run: pip install -r requirements-adk.txt"
        ) from exc

    return Agent(
        name="care_compass_coordinator",
        model=os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        instruction=(
            "You are the CareCompass coordinator. Use the create_plan tool for "
            "student or community support navigation. Do not request secrets, "
            "do not provide medical or legal advice, and escalate crisis cases."
        ),
        tools=[create_plan],
    )


try:
    root_agent = build_root_agent()
except RuntimeError:
    root_agent = None


if __name__ == "__main__":
    if root_agent is None:
        raise SystemExit("Install optional ADK dependencies to run this entrypoint.")
    print("ADK root_agent is ready: care_compass_coordinator")
