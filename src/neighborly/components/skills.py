"""Skill system.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neighborly.components.stats import Stat
from neighborly.defs.base_types import SkillDef
from neighborly.ecs import Component

SKILL_MIN_VALUE = 0
"""The lowest value a skill stat can be."""

SKILL_MAX_VALUE = 255
"""The highest value a skill stat can be."""


class Skill(Component):
    """A skill that a character can have and improve."""

    __slots__ = ("definition",)

    definition: SkillDef
    """The definition for this skill."""

    def __init__(self, definition: SkillDef) -> None:
        super().__init__()
        self.definition = definition

    @property
    def definition_id(self) -> str:
        """The ID of this skill's definition."""
        return self.definition.definition_id

    @property
    def display_name(self) -> str:
        """The name of this skill."""
        return self.definition.display_name

    @property
    def description(self) -> str:
        """A short description of the skill."""
        return self.definition.description

    def to_dict(self) -> dict[str, Any]:
        return {"definition_id": self.definition_id}

    def __str__(self) -> str:
        return f"Skill(definition_id={self.definition_id!r})"

    def __repr__(self) -> str:
        return f"Skill(definition_id={self.definition_id!r})"


@dataclass
class SkillInstance:
    """An instance of a skill being attached to a GameObject."""

    skill: Skill
    stat: Stat

    def __str__(self) -> str:
        return (
            f"SkillInstance(skill={self.skill.definition_id!r}, "
            f"value={self.stat.value!r})"
        )

    def __repr__(self) -> str:
        return (
            f"SkillInstance(skill={self.skill.definition_id!r}, "
            f"value={self.stat.value!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return as serialized dict."""
        return {
            "skill": self.skill.definition_id,
            "stat": self.stat.to_dict(),
        }


class Skills(Component):
    """Tracks skills stats for a character."""

    __slots__ = ("skills",)

    skills: dict[str, SkillInstance]
    """Skill names mapped to scores."""

    def __init__(self) -> None:
        super().__init__()
        self.skills = {}

    def add_skill(self, skill: Skill, base_value: float = 0.0) -> bool:
        """Add a new skill to the skill tracker."""
        if skill.definition_id not in self.skills:

            self.skills[skill.definition_id] = SkillInstance(
                skill=skill,
                stat=Stat(
                    base_value=base_value, bounds=(SKILL_MIN_VALUE, SKILL_MAX_VALUE)
                ),
            )

            return True

        return False

    def __str__(self) -> str:
        skill_value_pairs = {
            skill_id: skill_instance.stat.value
            for skill_id, skill_instance in self.skills.items()
        }
        return f"Skills({repr(skill_value_pairs)})"

    def __repr__(self) -> str:
        skill_value_pairs = {
            skill_id: skill_instance.stat.value
            for skill_id, skill_instance in self.skills.items()
        }
        return f"Skills({repr(skill_value_pairs)})"

    def to_dict(self) -> dict[str, Any]:
        return {"skills": [s.to_dict() for s in self.skills.values()]}
