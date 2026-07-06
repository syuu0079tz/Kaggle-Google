"""Resource catalog loading and search."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import Resource


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = PROJECT_ROOT / "data" / "resources.json"


def load_resources(path: Path | str | None = None) -> list[Resource]:
    catalog_path = Path(path) if path else DEFAULT_CATALOG
    with catalog_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return [Resource.from_dict(item) for item in raw["resources"]]


def _score_resource(resource: Resource, query: str, tags: Iterable[str], location: str) -> int:
    haystack = " ".join(
        [
            resource.name,
            resource.category,
            resource.location,
            " ".join(resource.tags),
            resource.eligibility,
            resource.safety_notes,
        ]
    ).lower()
    query_terms = [term for term in query.lower().split() if len(term) > 2]
    score = 0

    for tag in tags:
        if tag in resource.tags:
            score += 8

    for term in query_terms:
        if term in haystack:
            score += 1

    if location and location.lower() in resource.location.lower():
        score += 3
    if "online" in resource.location.lower():
        score += 2
    if "crisis" in tags and ("crisis" in resource.tags or "emergency" in resource.tags):
        score += 10
    return score


def search_resources(
    query: str,
    tags: list[str] | None = None,
    location: str = "",
    limit: int = 5,
    catalog_path: Path | str | None = None,
) -> list[dict[str, object]]:
    resources = load_resources(catalog_path)
    tags = tags or []
    scored = [
        (_score_resource(resource, query=query, tags=tags, location=location), resource)
        for resource in resources
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    positive = [(score, resource) for score, resource in scored if score > 0]

    selected: dict[str, tuple[int, Resource]] = {}
    for tag in tags:
        specialized = [
            (score, resource)
            for score, resource in positive
            if tag in resource.tags and resource.id != "monash-connect"
        ]
        fallback = [
            (score, resource)
            for score, resource in positive
            if tag in resource.tags
        ]
        for score, resource in specialized or fallback:
            if resource.id not in selected:
                selected[resource.id] = (score, resource)
                break

    for score, resource in positive:
        if len(selected) >= limit:
            break
        selected.setdefault(resource.id, (score, resource))

    ranked = sorted(selected.values(), key=lambda item: item[0], reverse=True)
    return [
        {"score": score, **resource.to_dict()}
        for score, resource in ranked
    ][:limit]


def get_resource(resource_id: str, catalog_path: Path | str | None = None) -> dict[str, object] | None:
    for resource in load_resources(catalog_path):
        if resource.id == resource_id:
            return resource.to_dict()
    return None
