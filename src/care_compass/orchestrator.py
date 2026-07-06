"""Public orchestration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .agents import CareCompassOrchestrator
from .tools import ToolRegistry


def run_agent(user_text: str, catalog_path: Path | str | None = None) -> dict[str, Any]:
    tools = ToolRegistry(catalog_path=catalog_path)
    return CareCompassOrchestrator(tools=tools).run(user_text)

