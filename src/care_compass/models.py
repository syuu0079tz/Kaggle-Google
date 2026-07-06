"""Shared data models for the CareCompass agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Resource:
    """A public support resource from the local catalog."""

    id: str
    name: str
    category: str
    location: str
    tags: list[str]
    eligibility: str
    contact: str
    url: str
    hours: str
    safety_notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Resource":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            category=str(data["category"]),
            location=str(data["location"]),
            tags=list(data.get("tags", [])),
            eligibility=str(data.get("eligibility", "")),
            contact=str(data.get("contact", "")),
            url=str(data.get("url", "")),
            hours=str(data.get("hours", "")),
            safety_notes=str(data.get("safety_notes", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "location": self.location,
            "tags": self.tags,
            "eligibility": self.eligibility,
            "contact": self.contact,
            "url": self.url,
            "hours": self.hours,
            "safety_notes": self.safety_notes,
        }


@dataclass
class AgentTrace:
    """A safe trace entry for judging and debugging."""

    agent: str
    action: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"agent": self.agent, "action": self.action, "details": self.details}

