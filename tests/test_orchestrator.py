from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from care_compass.orchestrator import run_agent


class OrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env_patcher = patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "",
                "GOOGLE_API_KEY": "",
                "GOOGLE_GENERATIVE_AI_API_KEY": "",
                "GOOGLE_GENAI_API_KEY": "",
            },
        )
        self.env_patcher.start()

    def tearDown(self) -> None:
        self.env_patcher.stop()

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

    def test_model_review_agent_is_reported_without_api_key(self) -> None:
        result = run_agent("I need academic help with an assignment.")
        self.assertEqual(result["model_review"]["status"], "skipped_no_api_key")
        self.assertIn(
            "model_review_agent",
            {trace["agent"] for trace in result["agent_trace"]},
        )

    def test_next_steps_are_tailored_to_detected_needs(self) -> None:
        academic = run_agent("I am behind on an assignment and have an exam deadline.")
        housing = run_agent("My landlord mentioned eviction and I need housing support.")

        self.assertNotEqual(academic["next_steps"], housing["next_steps"])
        self.assertTrue(
            any("course" in step.lower() or "exam" in step.lower() for step in academic["next_steps"])
        )
        self.assertTrue(
            any("housing" in step.lower() or "tenancy" in step.lower() for step in housing["next_steps"])
        )


if __name__ == "__main__":
    unittest.main()
