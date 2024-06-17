"""Skill system.

"""

from __future__ import annotations

from typing import Any

import attrs

from neighborly.components.stats import Stat
from neighborly.ecs import Component

SKILL_MIN_VALUE = 0
"""The lowest value a skill stat can be."""

SKILL_MAX_VALUE = 255
"""The highest value a skill stat can be."""


@attrs.define
class Skill:
    """Defines a skill that a character can learn."""

    definition_id: str
    """A unique ID for this skill among other skills."""
    name: str
    """A regular text name."""
    description: str = ""
    """A short description of the skill."""
    tags: set[str] = attrs.field(factory=set)
    """A set of tags associated with this skill."""


class SkillInstance:
    """An instance of a skill associated with a character."""

    __slots__ = ("skill", "stat")

    def __init__(self, skill: Skill, base_value: float = 0.0) -> None:
        self.skill = skill
        self.stat = Stat(
            base_value=base_value, bounds=(SKILL_MIN_VALUE, SKILL_MAX_VALUE)
        )

    def __str__(self) -> str:
        return (
            f"SkillInstance(skill={self.skill.definition_id!r}, "
            f"value={self.stat.value!r}, base_value={self.stat.base_value!r})"
        )

    def __repr__(self) -> str:
        return (
            f"SkillInstance(skill={self.skill.definition_id!r}, "
            f"value={self.stat.value!r}, base_value={self.stat.base_value!r})"
        )


class Skills(Component):
    """Tracks skills stats for a character."""

    __slots__ = ("skills",)

    skills: dict[str, SkillInstance]
    """Skill names mapped to scores."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.skills = {}

    def get_skill(self, skill_id: str) -> SkillInstance:
        """Get a skill by ID."""
        return self.skills[skill_id]

    def add_skill(self, skill: Skill, base_value: float = 0.0) -> bool:
        """Add a new skill to the skill tracker."""
        if skill.definition_id not in self.skills:

            self.skills[skill.definition_id] = SkillInstance(
                skill, base_value=base_value
            )

            return True

        return False

    def __str__(self) -> str:
        skill_value_pairs = {
            skill_id: skill.stat.value for skill_id, skill in self.skills.items()
        }
        return f"Skills({repr(skill_value_pairs)})"

    def __repr__(self) -> str:
        skill_value_pairs = {
            skill_id: skill.stat.value for skill_id, skill in self.skills.items()
        }
        return f"Skills({repr(skill_value_pairs)})"

    def to_dict(self) -> dict[str, Any]:
        skill_value_pairs = {
            skill_id: skill.stat.value for skill_id, skill in self.skills.items()
        }
        return {"skills": skill_value_pairs}
