"""Gemini review agent integration.

The core routing workflow must stay reproducible and truthful without external
services. When a Gemini API key is configured, this module asks Gemini to review
the already-built plan without allowing it to create new contact details.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_FALLBACK_MODELS = ("gemini-2.0-flash", "gemini-1.5-flash")
API_KEY_ENV_NAMES = (
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
    "GOOGLE_GENAI_API_KEY",
)
INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
GENERATE_CONTENT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
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


def gemini_candidate_models() -> list[str]:
    configured = [gemini_model_name()]
    configured.extend(
        item.strip()
        for item in os.environ.get("GEMINI_FALLBACK_MODELS", "").split(",")
        if item.strip()
    )
    configured.extend(DEFAULT_FALLBACK_MODELS)

    models: list[str] = []
    for model in configured:
        if model not in models:
            models.append(model)
    return models


def gemini_api_key() -> str:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    return ""


def gemini_api_key_configured() -> bool:
    return bool(gemini_api_key())


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

    candidates = response.get("candidates", [])
    if isinstance(candidates, list):
        for candidate in candidates:
            parts = candidate.get("content", {}).get("parts", [])
            if isinstance(parts, list):
                text_parts = [
                    part.get("text", "").strip()
                    for part in parts
                    if isinstance(part.get("text"), str) and part.get("text", "").strip()
                ]
                if text_parts:
                    return "\n".join(text_parts)

    fragments: list[str] = []
    for step in response.get("steps", []):
        for item in step.get("output", []):
            text = item.get("text")
            if isinstance(text, str):
                fragments.append(text)
    return "\n".join(fragment.strip() for fragment in fragments if fragment.strip())


def _contains_contact_like_text(text: str) -> bool:
    return bool(URL_RE.search(text) or EMAIL_RE.search(text) or PHONE_RE.search(text))


def _post_json(url: str, body: dict[str, Any], api_key: str, timeout_seconds: int) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _interactions_body(model: str, plan: dict[str, Any], redacted_request: str) -> dict[str, Any]:
    return {
        "model": model,
        "system_instruction": SYSTEM_INSTRUCTION,
        "input": _review_payload(plan, redacted_request),
        "generation_config": {
            "temperature": 0.1,
            "thinking_level": "low",
        },
    }


def _generate_content_body(plan: dict[str, Any], redacted_request: str) -> dict[str, Any]:
    return {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _review_payload(plan, redacted_request)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
        },
    }


def _generate_content_url(model: str) -> str:
    return f"{GENERATE_CONTENT_BASE_URL}/{quote(model, safe='')}:generateContent"


def _call_gemini(
    plan: dict[str, Any],
    redacted_request: str,
    api_key: str,
    timeout_seconds: int,
) -> tuple[str, str, str, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []

    primary_model = gemini_model_name()
    try:
        payload = _post_json(
            INTERACTIONS_URL,
            _interactions_body(primary_model, plan, redacted_request),
            api_key,
            timeout_seconds,
        )
        return _extract_output_text(payload), primary_model, "interactions", attempts
    except HTTPError as exc:
        attempts.append({"route": "interactions", "model": primary_model, "status": exc.code})

    for model in gemini_candidate_models():
        try:
            payload = _post_json(
                _generate_content_url(model),
                _generate_content_body(plan, redacted_request),
                api_key,
                timeout_seconds,
            )
            return _extract_output_text(payload), model, "generateContent", attempts
        except HTTPError as exc:
            attempts.append({"route": "generateContent", "model": model, "status": exc.code})

    return "", primary_model, "unavailable", attempts


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
    api_key = gemini_api_key()
    if not api_key:
        return {
            "enabled": False,
            "provider": "Google Gemini",
            "model": model,
            "status": "skipped_no_api_key",
            "summary": "",
            "message": "Set GEMINI_API_KEY or GOOGLE_API_KEY to enable the Gemini model review agent.",
        }

    try:
        summary, used_model, route, attempts = _call_gemini(
            plan,
            redacted_request,
            api_key,
            timeout_seconds,
        )
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

    if not summary:
        attempt_message = ", ".join(
            f"{item['route']}:{item['model']}={item['status']}" for item in attempts
        )
        return {
            "enabled": True,
            "provider": "Google Gemini",
            "model": model,
            "status": "model_http_error" if attempts else "empty_model_response",
            "summary": "",
            "message": f"Gemini review unavailable. Attempts: {attempt_message or 'empty response'}.",
        }
    if _contains_contact_like_text(summary):
        return {
            "enabled": True,
            "provider": "Google Gemini",
            "model": used_model,
            "status": "blocked_contact_like_text",
            "summary": "",
            "message": "Gemini review was hidden because it included contact-like text.",
        }

    return {
        "enabled": True,
        "provider": "Google Gemini",
        "model": used_model,
        "status": "ok",
        "summary": summary,
        "message": f"Gemini model review completed through {route}.",
    }
