"""Allowlisted tool registry shared by agents and MCP servers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .catalog import get_resource, search_resources
from .security import analyze_request


class ToolRegistry:
    """A small allowlisted tool broker.

    The registry prevents agents from inventing tools or calling arbitrary code.
    This is deliberately simple so the security behavior is easy to inspect.
    """

    def __init__(self, catalog_path: Path | str | None = None) -> None:
        self.catalog_path = catalog_path
        self._tools: dict[str, Callable[..., Any]] = {
            "search_resources": self._search_resources,
            "get_resource": self._get_resource,
            "safety_check": self._safety_check,
        }

    @property
    def names(self) -> list[str]:
        return sorted(self._tools)

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise PermissionError(f"Tool is not allowlisted: {name}")
        return self._tools[name](**arguments)

    def _search_resources(
        self,
        query: str,
        tags: list[str] | None = None,
        location: str = "",
        limit: int = 5,
    ) -> list[dict[str, object]]:
        return search_resources(
            query=query,
            tags=tags or [],
            location=location,
            limit=limit,
            catalog_path=self.catalog_path,
        )

    def _get_resource(self, resource_id: str) -> dict[str, object] | None:
        return get_resource(resource_id=resource_id, catalog_path=self.catalog_path)

    def _safety_check(self, text: str) -> dict[str, object]:
        return analyze_request(text).to_dict()

