"""Progressive disclosure loader for local agent skills."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = PROJECT_ROOT / "skills"


@lru_cache(maxsize=16)
def load_skill(skill_name: str) -> str:
    path = SKILLS_ROOT / skill_name / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"Skill not found: {skill_name}")
    return path.read_text(encoding="utf-8")


def skill_summary(skill_name: str) -> str:
    text = load_skill(skill_name)
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return f"{skill_name} skill loaded"

