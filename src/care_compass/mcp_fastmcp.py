"""Official MCP SDK server path using FastMCP when installed."""

from __future__ import annotations

from .tools import ToolRegistry


registry = ToolRegistry()

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - optional dependency path.
    raise RuntimeError("Install optional dependencies: pip install -r requirements-adk.txt") from exc


mcp = FastMCP("care-compass-agent")


@mcp.tool()
def search_resources(query: str, tags: list[str] | None = None, location: str = "", limit: int = 5):
    """Search the public support resource catalog."""

    return registry.call(
        "search_resources",
        {"query": query, "tags": tags or [], "location": location, "limit": limit},
    )


@mcp.tool()
def safety_check(text: str):
    """Redact PII and identify safety flags."""

    return registry.call("safety_check", {"text": text})


@mcp.tool()
def get_resource(resource_id: str):
    """Return one catalog resource by id."""

    return registry.call("get_resource", {"resource_id": resource_id})


if __name__ == "__main__":
    mcp.run()

