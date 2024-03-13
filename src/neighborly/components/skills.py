"""Skill system.

"""

from __future__ import annotations

from typing import Any

import attrs

from neighborly.components.stats import OnStatUpdate, Stat
from neighborly.ecs import Component
from neighborly.ecs.event import Event
from neighborly.ecs.game_object import GameObject


@attrs.define
class OnSkillChange(Event):
    """Event emitted when a skill value changes."""

    gameobject: GameObject
    skill: SkillInstance
    value: float


class Skill(Component):
    """A skill that a character can have and improve."""

    __slots__ = (
        "_definition_id",
        "_description",
        "_display_name",
    )

    _definition_id: str
    """The ID of this tag definition."""
    _description: str
    """A short description of the tag."""
    _display_name: str
    """The name of this tag printed."""

    def __init__(
        self,
        definition_id: str,
        display_name: str,
        description: str,
    ) -> None:
        super().__init__()
        self._definition_id = definition_id
        self._display_name = display_name
        self._description = description

    @property
    def definition_id(self) -> str:
        """The ID of this tag definition."""
        return self._definition_id

    @property
    def display_name(self) -> str:
        """The name of this tag printed."""
        return self._display_name

    @property
    def description(self) -> str:
        """A short description of the tag."""
        return self._description

    def __str__(self) -> str:
        return self.definition_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "display_name": self.display_name,
            "description": self.description,
        }


class SkillInstance:
    """A record of a skill attached to a GameObject."""

    __slots__ = (
        "skill",
        "stat",
    )

    skill: Skill
    """The skill this is an instance of."""
    stat: Stat
    """The current stat for this skill."""
    data: dict[str, Any]
    """General key-value data store for the trait."""

    def __init__(self, skill: Skill, value: float = 0) -> None:
        self.skill = skill
        self.stat = Stat(value, (0, 250), is_discrete=True)


class Skills(Component):
    """Tracks skills stats for a character."""

    __slots__ = ("skills",)

    skills: dict[str, SkillInstance]
    """This GameObjects skill stats."""

    def __init__(self) -> None:
        super().__init__()
        self.skills = {}

    def has_skill(self, skill: str) -> bool:
        """Check if a character has a skill.

        Parameters
        ----------
        skill
            The skill to check for.

        Returns
        -------
        bool
            True if the skill is present, False otherwise.
        """
        return skill in self.skills

    def add_skill(self, skill: Skill, base_value: float = 0.0) -> None:
        """Add a new skill to the skill tracker."""
        if skill.definition_id not in self.skills:
            skill_instance = SkillInstance(skill, base_value)
            skill_instance.stat.on_value_change.add_listener(
                self._handle_skill_change(skill.definition_id)
            )
            self.skills[skill.definition_id] = skill_instance
        else:
            return

    def get_skill(self, skill: str) -> SkillInstance:
        """Get the stat for a skill.

        Parameters
        ----------
        skill
            The skill to get the stat for.
        """
        return self.skills[skill]

    def _handle_skill_change(self, skill_id: str):
        """Wrapper function to capture skill ID for actual handler."""

        def event_handler(_: object, event: OnStatUpdate):
            self.gameobject.world.events.dispatch_event(
                OnSkillChange(
                    gameobject=self.gameobject,
                    skill=self.get_skill(skill_id),
                    value=event.value,
                )
            )

        return event_handler

    def __str__(self) -> str:
        skill_value_pairs = {k: v.stat.value for k, v in self.skills.items()}
        return f"Skills({skill_value_pairs})"

    def __repr__(self) -> str:
        skill_value_pairs = {k: v.stat.value for k, v in self.skills.items()}
        return f"Skills({skill_value_pairs})"

    def to_dict(self) -> dict[str, Any]:
        return {k: v.stat.value for k, v in self.skills.items()}
