"""Skill system.

"""

from __future__ import annotations

from typing import Any, Iterator, Mapping

from neighborly.components.stats import Stat
from neighborly.ecs import Component, GameObject


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


class Skills(Component):
    """Tracks skills stats for a character."""

    __slots__ = ("_skills",)

    _skills: dict[GameObject, Stat]
    """Skill names mapped to scores."""

    def __init__(self) -> None:
        super().__init__()
        self._skills = {}

    @property
    def skills(self) -> Mapping[GameObject, Stat]:
        """Get skills."""
        return self._skills

    def has_skill(self, skill: GameObject) -> bool:
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
        return skill in self._skills

    def add_skill(self, skill: GameObject, base_value: float = 0.0) -> None:
        """Add a new skill to the skill tracker."""
        if skill not in self._skills:
            self._skills[skill] = Stat(base_value=base_value, bounds=(0, 255))
        else:
            return

    def get_skill(self, skill: GameObject) -> Stat:
        """Get the stat for a skill.

        Parameters
        ----------
        skill
            The skill to get the stat for.
        """
        return self._skills[skill]

    def __getitem__(self, item: GameObject) -> Stat:
        """Get the value of a skill."""
        return self.get_skill(item)

    def __str__(self) -> str:
        skill_value_pairs = {
            skill.name: stat.value for skill, stat in self._skills.items()
        }
        return f"{type(self).__name__}({skill_value_pairs})"

    def __repr__(self) -> str:
        skill_value_pairs = {
            skill.name: stat.value for skill, stat in self._skills.items()
        }
        return f"{type(self).__name__}({skill_value_pairs})"

    def __iter__(self) -> Iterator[tuple[GameObject, Stat]]:
        return iter(self._skills.items())

    def to_dict(self) -> dict[str, Any]:
        return {**{skill.name: stat.value for skill, stat in self._skills.items()}}
