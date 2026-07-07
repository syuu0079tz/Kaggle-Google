from __future__ import annotations

import os
import json
import unittest
from unittest.mock import patch

from care_compass.gemini import DEFAULT_GEMINI_MODEL, generate_model_review


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class GeminiReviewTests(unittest.TestCase):
    def test_review_is_disabled_without_api_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            review = generate_model_review({"recommendations": []}, "redacted request")

        self.assertFalse(review["enabled"])
        self.assertEqual(review["model"], DEFAULT_GEMINI_MODEL)
        self.assertEqual(review["status"], "skipped_no_api_key")

    def test_review_uses_gemini_when_api_key_is_configured(self) -> None:
        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GEMINI_MODEL": "test-model"}, clear=True),
            patch(
                "care_compass.gemini.urlopen",
                return_value=FakeResponse({"output_text": "- fit: good\n- verification: official page\n- safety boundary: no advice"}),
            ) as urlopen_mock,
        ):
            review = generate_model_review({"recommendations": []}, "redacted request")

        self.assertTrue(review["enabled"])
        self.assertEqual(review["model"], "test-model")
        self.assertEqual(review["status"], "ok")
        self.assertIn("fit", review["summary"])
        urlopen_mock.assert_called_once()

    def test_review_blocks_contact_like_model_output(self) -> None:
        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True),
            patch(
                "care_compass.gemini.urlopen",
                return_value=FakeResponse({"output_text": "Call +61 3 9902 6011 for help."}),
            ),
        ):
            review = generate_model_review({"recommendations": []}, "redacted request")

        self.assertEqual(review["status"], "blocked_contact_like_text")
        self.assertEqual(review["summary"], "")


if __name__ == "__main__":
    unittest.main()
