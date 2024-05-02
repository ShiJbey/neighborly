"""Skill system.

"""

from __future__ import annotations

from typing import Any, cast

from neighborly.components.stats import Stat, StatValueChangeEvent
from neighborly.ecs import Component, GameObject

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
        gameobject: GameObject,
    ) -> None:
        super().__init__(gameobject)
        self.skills = {}

    def add_skill(self, skill: str, base_value: float = 0.0) -> bool:
        """Add a new skill to the skill tracker."""
        if skill not in self.skills:

            skill_stat = Stat(
                base_value=base_value, bounds=(SKILL_MIN_VALUE, SKILL_MAX_VALUE)
            )

            self.skills[skill] = skill_stat

            skill_stat.on_value_changed.add_listener(
                self.handle_stat_value_change(skill)
            )

            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.skills.{skill}!{skill_stat.value}"
            )

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

    def handle_stat_value_change(self, skill_id: str):
        """Wraps a listener function for stat value change events."""

        # this is necessary to capture the stat ID in a closure
        def handler(source: object, event: StatValueChangeEvent) -> None:
            source = cast(Stat, source)

            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.skills.{skill_id}!{event.value}"
            )

        return handler
