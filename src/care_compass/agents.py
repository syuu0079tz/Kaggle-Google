"""Deterministic multi-agent implementation for the core demo."""

from __future__ import annotations

from typing import Any

from .models import AgentTrace
from .security import SafetyReport, analyze_request
from .skills import skill_summary
from .tools import ToolRegistry


NEED_KEYWORDS: dict[str, tuple[str, ...]] = {
    "academic": ("exam", "assignment", "study", "grade", "lecture", "course", "tutor", "behind"),
    "wellbeing": ("anxious", "stress", "panic", "sad", "depressed", "counsel", "mental", "wellbeing"),
    "finance": ("rent", "money", "fee", "tuition", "food", "job", "financial", "bills", "scholarship"),
    "housing": ("housing", "rent", "landlord", "room", "eviction", "accommodation"),
    "international": ("international", "visa", "overseas", "language", "passport"),
    "accessibility": ("disability", "accessibility", "adjustment", "accommodation", "chronic"),
    "career": ("career", "resume", "internship", "job", "interview"),
    "health": ("clinic", "doctor", "health", "medication", "sick"),
    "legal": ("legal", "tenant", "contract", "visa breach", "immigration"),
    "crisis": ("emergency", "suicide", "self harm", "self-harm", "unsafe", "abuse", "overdose"),
}


def _infer_needs(text: str) -> list[str]:
    lower_text = text.lower()
    needs = [
        need
        for need, keywords in NEED_KEYWORDS.items()
        if any(keyword in lower_text for keyword in keywords)
    ]
    return needs or ["general_support"]


def _infer_location(text: str) -> str:
    lower_text = text.lower()
    if "campus" in lower_text or "university" in lower_text or "student" in lower_text:
        return "campus"
    if "online" in lower_text or "remote" in lower_text:
        return "online"
    return "online"


class IntakeAgent:
    name = "intake_agent"
    skill_name = "intake_safety"

    def run(self, user_text: str) -> tuple[dict[str, Any], SafetyReport, AgentTrace]:
        safety = analyze_request(user_text)
        redacted_text = safety.redacted_text
        needs = _infer_needs(redacted_text)
        urgency = "high" if "crisis" in needs or safety.requires_human_review else "normal"
        intake = {
            "redacted_request": redacted_text,
            "needs": needs,
            "location": _infer_location(redacted_text),
            "urgency": urgency,
            "skill_loaded": skill_summary(self.skill_name),
        }
        trace = AgentTrace(
            agent=self.name,
            action="classified_request",
            details={"needs": needs, "urgency": urgency, "safety_flags": safety.flags},
        )
        return intake, safety, trace


class ResourceMatcherAgent:
    name = "resource_matcher_agent"
    skill_name = "resource_matching"

    def __init__(self, tools: ToolRegistry) -> None:
        self.tools = tools

    def run(self, intake: dict[str, Any]) -> tuple[list[dict[str, object]], AgentTrace]:
        matches = self.tools.call(
            "search_resources",
            {
                "query": intake["redacted_request"],
                "tags": intake["needs"],
                "location": intake["location"],
                "limit": 5,
            },
        )
        trace = AgentTrace(
            agent=self.name,
            action="called_allowlisted_tool",
            details={
                "tool": "search_resources",
                "result_count": len(matches),
                "skill_loaded": skill_summary(self.skill_name),
            },
        )
        return matches, trace


class PlannerAgent:
    name = "planner_agent"
    skill_name = "followup_plan"

    def run(
        self,
        intake: dict[str, Any],
        matches: list[dict[str, object]],
        safety: SafetyReport,
    ) -> tuple[dict[str, Any], AgentTrace]:
        next_steps: list[str] = []
        if safety.requires_human_review:
            next_steps.append(
                "If there is immediate danger, contact local emergency services or a crisis line now."
            )

        if matches:
            top = matches[0]
            next_steps.append(
                f"Start with {top['name']} because it best matches {', '.join(intake['needs'])}."
            )
            next_steps.append("Prepare only the minimum details needed: current need, deadline, and preferred contact method.")
            next_steps.append("After contacting the first resource, use the second recommendation as a backup path.")
        else:
            next_steps.append("Contact a general student services desk and ask for referral routing.")

        next_steps.append("Do not share passwords, API keys, bank details, or private documents in this demo.")

        plan = {
            "summary": "A privacy-first support navigation plan.",
            "needs": intake["needs"],
            "urgency": intake["urgency"],
            "recommendations": matches,
            "next_steps": next_steps,
            "skill_loaded": skill_summary(self.skill_name),
        }
        trace = AgentTrace(
            agent=self.name,
            action="created_action_plan",
            details={"step_count": len(next_steps), "recommendation_count": len(matches)},
        )
        return plan, trace


class SafetyReviewerAgent:
    name = "safety_reviewer_agent"
    skill_name = "intake_safety"

    def run(
        self,
        plan: dict[str, Any],
        safety: SafetyReport,
    ) -> tuple[dict[str, Any], AgentTrace]:
        notices: list[str] = [
            "This project is a routing assistant, not a medical, legal, financial, or emergency service.",
            "Contacts come from public resource pages; verify current details on the official URL before acting.",
        ]
        if "prompt_injection_attempt" in safety.flags:
            notices.append("A prompt-injection attempt was detected and ignored.")
        if safety.requires_human_review:
            notices.append("Human review is recommended before relying on this plan.")

        final = {
            **plan,
            "safety": {
                "flags": safety.flags,
                "requires_human_review": safety.requires_human_review,
                "notices": notices,
                "rationale": safety.rationale,
                "skill_loaded": skill_summary(self.skill_name),
            },
        }
        trace = AgentTrace(
            agent=self.name,
            action="reviewed_plan",
            details={
                "flags": safety.flags,
                "requires_human_review": safety.requires_human_review,
            },
        )
        return final, trace


class CareCompassOrchestrator:
    """Sequential multi-agent workflow."""

    def __init__(self, tools: ToolRegistry | None = None) -> None:
        self.tools = tools or ToolRegistry()
        self.intake_agent = IntakeAgent()
        self.matcher_agent = ResourceMatcherAgent(self.tools)
        self.planner_agent = PlannerAgent()
        self.safety_agent = SafetyReviewerAgent()

    def run(self, user_text: str) -> dict[str, Any]:
        traces: list[AgentTrace] = []
        intake, safety, trace = self.intake_agent.run(user_text)
        traces.append(trace)

        matches, trace = self.matcher_agent.run(intake)
        traces.append(trace)

        plan, trace = self.planner_agent.run(intake, matches, safety)
        traces.append(trace)

        final, trace = self.safety_agent.run(plan, safety)
        traces.append(trace)

        final["redacted_request"] = intake["redacted_request"]
        final["agent_trace"] = [item.to_dict() for item in traces]
        final["tool_allowlist"] = self.tools.names
        return final
