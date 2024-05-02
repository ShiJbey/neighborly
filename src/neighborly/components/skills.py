"""Skill system.

"""

from __future__ import annotations

from typing import Any

from neighborly.components.stats import Stat
from neighborly.ecs import Component

SKILL_MIN_VALUE = 0
"""The lowest value a skill stat can be."""

SKILL_MAX_VALUE = 255
"""The highest value a skill stat can be."""


class Skills(Component):
    """Tracks skills stats for a character."""

    __slots__ = ("skills",)

    skills: dict[str, Stat]
    """Skill names mapped to scores."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.skills = {}

    def add_skill(self, skill: str, base_value: float = 0.0) -> bool:
        """Add a new skill to the skill tracker."""
        if skill not in self.skills:

            skill_stat = Stat(
                base_value=base_value, bounds=(SKILL_MIN_VALUE, SKILL_MAX_VALUE)
            )

            self.skills[skill] = skill_stat

            return True

        return False

    def __str__(self) -> str:
        skill_value_pairs = {
            skill_id: stat.value for skill_id, stat in self.skills.items()
        }
        return f"Skills({repr(skill_value_pairs)})"

    def __repr__(self) -> str:
        skill_value_pairs = {
            skill_id: stat.value for skill_id, stat in self.skills.items()
        }
        return f"Skills({repr(skill_value_pairs)})"

    def to_dict(self) -> dict[str, Any]:
        return {"skills": [s.to_dict() for s in self.skills.values()]}
