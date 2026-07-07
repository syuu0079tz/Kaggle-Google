"""Optional Gemini review agent integration.

The core routing workflow must stay reproducible and truthful without external
services. When GEMINI_API_KEY is configured, this module asks Gemini to review
the already-built plan without allowing it to create new contact details.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
URL_RE = re.compile(r"https?://\S+|\bwww\.\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()/-]{7,}\d)(?!\d)")


SYSTEM_INSTRUCTION = (
    "You are the CareCompass Model Review Agent. Review the provided support-routing "
    "plan only. Do not add, invent, infer, or guess service names, phone numbers, "
    "emails, URLs, opening hours, eligibility rules, or official advice. Do not give "
    "medical, legal, visa, financial, or emergency advice. If a detail is not present "
    "in the JSON, say to verify it on the official URL already shown by the app. "
    "Return three concise bullets: fit, verification, safety boundary."
)


def gemini_model_name() -> str:
    return os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL


def gemini_api_key_configured() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


def _review_payload(plan: dict[str, Any], redacted_request: str) -> str:
    recommendations = [
        {
            "name": item.get("name", ""),
            "category": item.get("category", ""),
            "location": item.get("location", ""),
            "url": item.get("url", ""),
            "contact": item.get("contact", ""),
            "hours": item.get("hours", ""),
            "safety_notes": item.get("safety_notes", ""),
        }
        for item in plan.get("recommendations", [])
    ]
    review_context = {
        "redacted_request": redacted_request,
        "detected_needs": plan.get("needs", []),
        "urgency": plan.get("urgency", ""),
        "recommendations": recommendations,
        "next_steps": plan.get("next_steps", []),
        "safety_notices": plan.get("safety", {}).get("notices", []),
    }
    return (
        "Review this CareCompass plan. Use only the JSON facts below. "
        "Do not repeat phone numbers, emails, or URLs in your answer.\n\n"
        + json.dumps(review_context, ensure_ascii=False, indent=2)
    )


def _extract_output_text(response: dict[str, Any]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str):
        return output_text.strip()

    fragments: list[str] = []
    for step in response.get("steps", []):
        for item in step.get("output", []):
            text = item.get("text")
            if isinstance(text, str):
                fragments.append(text)
    return "\n".join(fragment.strip() for fragment in fragments if fragment.strip())


def _contains_contact_like_text(text: str) -> bool:
    return bool(URL_RE.search(text) or EMAIL_RE.search(text) or PHONE_RE.search(text))


def generate_model_review(
    plan: dict[str, Any],
    redacted_request: str,
    timeout_seconds: int = 12,
) -> dict[str, Any]:
    """Return a Gemini review result, or a safe disabled/error status.

    The returned object is intentionally explicit so the web UI and trace can
    show whether an online model was called.
    """

    model = gemini_model_name()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {
            "enabled": False,
            "provider": "Google Gemini",
            "model": model,
            "status": "skipped_no_api_key",
            "summary": "",
            "message": "Set GEMINI_API_KEY to enable the Gemini model review agent.",
        }

    body = json.dumps(
        {
            "model": model,
            "system_instruction": SYSTEM_INSTRUCTION,
            "input": _review_payload(plan, redacted_request),
            "generation_config": {
                "temperature": 0.1,
                "thinking_level": "low",
            },
        }
    ).encode("utf-8")
    request = Request(
        INTERACTIONS_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return {
            "enabled": True,
            "provider": "Google Gemini",
            "model": model,
            "status": "model_http_error",
            "summary": "",
            "message": f"Gemini review unavailable: HTTP {exc.code}.",
        }
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "enabled": True,
            "provider": "Google Gemini",
            "model": model,
            "status": "model_error",
            "summary": "",
            "message": f"Gemini review unavailable: {type(exc).__name__}.",
        }

    summary = _extract_output_text(payload)
    if not summary:
        return {
            "enabled": True,
            "provider": "Google Gemini",
            "model": model,
            "status": "empty_model_response",
            "summary": "",
            "message": "Gemini returned no text for the model review.",
        }
    if _contains_contact_like_text(summary):
        return {
            "enabled": True,
            "provider": "Google Gemini",
            "model": model,
            "status": "blocked_contact_like_text",
            "summary": "",
            "message": "Gemini review was hidden because it included contact-like text.",
        }

    return {
        "enabled": True,
        "provider": "Google Gemini",
        "model": model,
        "status": "ok",
        "summary": summary,
        "message": "Gemini model review completed.",
    }
