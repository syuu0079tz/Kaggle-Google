"""Security and safety controls for the CareCompass agent."""

from __future__ import annotations

from dataclasses import dataclass, field
import re


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()/-]{7,}\d)(?!\d)")
STUDENT_ID_RE = re.compile(r"\b(?:student\s*id|sid|id)\s*[:#]?\s*[A-Z]?\d{6,12}\b", re.IGNORECASE)

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore (all )?(previous|above|system) instructions", re.IGNORECASE),
    re.compile(r"reveal (the )?(system prompt|developer message|hidden instructions)", re.IGNORECASE),
    re.compile(r"bypass (policy|guardrails|safety|security)", re.IGNORECASE),
    re.compile(r"print (all )?(api keys|passwords|secrets|tokens)", re.IGNORECASE),
    re.compile(r"run (shell|powershell|cmd|terminal)", re.IGNORECASE),
]

CRISIS_TERMS = {
    "suicide",
    "self harm",
    "self-harm",
    "kill myself",
    "hurt myself",
    "hurt someone",
    "overdose",
    "abuse",
    "unsafe at home",
    "emergency",
}

LEGAL_MEDICAL_TERMS = {
    "diagnosis",
    "prescribe",
    "medication dose",
    "legal advice",
    "visa breach",
    "immigration appeal",
}


@dataclass
class SafetyReport:
    """Result of security and safety screening."""

    redacted_text: str
    flags: list[str] = field(default_factory=list)
    requires_human_review: bool = False
    blocked: bool = False
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "redacted_text": self.redacted_text,
            "flags": self.flags,
            "requires_human_review": self.requires_human_review,
            "blocked": self.blocked,
            "rationale": self.rationale,
        }


def redact_pii(text: str) -> str:
    """Remove common PII from user text before it enters the agent trace."""

    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = PHONE_RE.sub("[REDACTED_PHONE]", text)
    text = STUDENT_ID_RE.sub("[REDACTED_STUDENT_ID]", text)
    return text


def detect_prompt_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in PROMPT_INJECTION_PATTERNS)


def _contains_any(text: str, terms: set[str]) -> bool:
    lower_text = text.lower()
    return any(term in lower_text for term in terms)


def analyze_request(text: str) -> SafetyReport:
    """Screen a request before planning.

    The app prefers safe continuation with escalation over silent failure. Prompt
    injection attempts are flagged and ignored; crisis cases are routed to human
    or emergency support language.
    """

    redacted = redact_pii(text)
    flags: list[str] = []
    rationale: list[str] = []
    requires_human_review = False

    if redacted != text:
        flags.append("pii_redacted")
        rationale.append("Contact details or identifiers were removed from the agent trace.")

    if detect_prompt_injection(text):
        flags.append("prompt_injection_attempt")
        rationale.append("Untrusted instructions were detected and ignored.")

    if _contains_any(text, CRISIS_TERMS):
        flags.append("crisis_or_immediate_risk")
        requires_human_review = True
        rationale.append("The request may involve immediate safety risk.")

    if _contains_any(text, LEGAL_MEDICAL_TERMS):
        flags.append("regulated_advice_boundary")
        requires_human_review = True
        rationale.append("The request may need qualified legal, medical, or immigration support.")

    return SafetyReport(
        redacted_text=redacted,
        flags=flags,
        requires_human_review=requires_human_review,
        blocked=False,
        rationale=rationale,
    )

