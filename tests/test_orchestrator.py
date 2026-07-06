from __future__ import annotations

import unittest

from care_compass.orchestrator import run_agent


class OrchestratorTests(unittest.TestCase):
    def test_student_finance_request_gets_recommendations_and_safe_trace(self) -> None:
        result = run_agent(
            "I am an international student behind on rent and anxious about exams. "
            "I do not know which Monash support service to contact first."
        )
        self.assertIn("international", result["needs"])
        self.assertIn("finance", result["needs"])
        self.assertGreaterEqual(len(result["recommendations"]), 3)
        for item in result["recommendations"]:
            self.assertTrue(str(item["url"]).startswith("https://"))
            self.assertNotIn("example.", str(item["url"]))
            self.assertNotIn("example.", str(item["contact"]))

    def test_tool_allowlist_is_reported(self) -> None:
        result = run_agent("I need academic help with an assignment.")
        self.assertEqual(
            set(result["tool_allowlist"]),
            {"get_resource", "safety_check", "search_resources"},
        )


if __name__ == "__main__":
    unittest.main()
