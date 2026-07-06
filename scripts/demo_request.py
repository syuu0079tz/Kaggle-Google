from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from care_compass.orchestrator import run_agent  # noqa: E402


REQUEST = (
    "I am a first-year international student. I am behind on rent, anxious about exams, "
    "and I do not know which campus service to contact first."
)


def main() -> int:
    print(json.dumps(run_agent(REQUEST), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
