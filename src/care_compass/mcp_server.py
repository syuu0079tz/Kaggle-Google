"""Dependency-free MCP-style JSON-RPC server over stdin/stdout.

This lightweight server exposes the same allowlisted tools used by the agents.
For the official MCP SDK path, see mcp_fastmcp.py.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from .tools import ToolRegistry


TOOLS = [
    {
        "name": "search_resources",
        "description": "Search the public support resource catalog.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "location": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_resource",
        "description": "Return one catalog resource by id.",
        "inputSchema": {
            "type": "object",
            "properties": {"resource_id": {"type": "string"}},
            "required": ["resource_id"],
        },
    },
    {
        "name": "safety_check",
        "description": "Redact PII and identify safety flags.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
]


class JsonRpcMcpServer:
    def __init__(self) -> None:
        self.tools = ToolRegistry()

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        request_id = message.get("id")
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2025-06-18",
                    "serverInfo": {"name": "care-compass-agent", "version": "0.1.0"},
                    "capabilities": {"tools": {}},
                }
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = message.get("params", {})
                name = params["name"]
                arguments = params.get("arguments", {})
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(self.tools.call(name, arguments), ensure_ascii=False),
                        }
                    ]
                }
            elif method == "notifications/initialized":
                return None
            else:
                return self._error(request_id, -32601, f"Method not found: {method}")
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:  # MCP clients expect structured errors.
            return self._error(request_id, -32000, str(exc))

    @staticmethod
    def _error(request_id: object, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def main() -> int:
    server = JsonRpcMcpServer()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = server.handle(json.loads(line))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

