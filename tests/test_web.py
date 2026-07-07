from __future__ import annotations

import unittest

from care_compass.security import redact_pii
from care_compass.web import render_page


class WebRenderingTests(unittest.TestCase):
    def test_result_page_does_not_echo_raw_private_details(self) -> None:
        raw_request = (
            "I am stressed about exams. I already tried calling "
            "+61 3 9902 6011 and 1300 22 4636."
        )
        html = render_page(request_text=redact_pii(raw_request)).decode("utf-8")
        self.assertNotIn("+61 3 9902 6011", html)
        self.assertNotIn("1300 22 4636", html)
        self.assertIn("[REDACTED_PHONE]", html)

    def test_page_css_wraps_long_result_text(self) -> None:
        html = render_page().decode("utf-8")
        self.assertIn("overflow-wrap: anywhere", html)
        self.assertIn("white-space: pre-wrap", html)
        self.assertIn("grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr)", html)


if __name__ == "__main__":
    unittest.main()
