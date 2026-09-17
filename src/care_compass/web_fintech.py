"""CareCompass web server with a dedicated FinTech classroom demo route."""

from __future__ import annotations

import argparse
import os
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .web import Handler as CareCompassHandler


REPO_ROOT = Path(__file__).resolve().parents[2]
FINTECH_DEMO = REPO_ROOT / "fintech-credit-demo" / "index.html"


class Handler(CareCompassHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/fintech-credit-demo", "/fintech-credit-demo/"}:
            try:
                body = FINTECH_DEMO.read_bytes()
            except OSError:
                self._send(
                    HTTPStatus.NOT_FOUND,
                    "text/plain; charset=utf-8",
                    b"FinTech demo not found",
                )
                return
            self._send(HTTPStatus.OK, "text/html; charset=utf-8", body)
            return
        super().do_GET()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run CareCompass with FinTech classroom demo route.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = parser.parse_args(argv)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"CareCompass Agent running at http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
