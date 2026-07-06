from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from care_compass.evaluation import run_evaluations  # noqa: E402


def main() -> int:
    report = run_evaluations()
    print(json.dumps({"passed": report["passed"], "total": report["total"]}, indent=2))
    for item in report["results"]:
        status = "PASS" if item["passed"] else "FAIL"
        print(f"{status} {item['id']}: {item['checks']}")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

