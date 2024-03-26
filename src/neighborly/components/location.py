"""Location Preference System.

This module contains classes and functions that help characters decide where within the
settlement they spend most of their time. Since the simulation does not model
characters' positions throughout the settlement, this is a way of tracking who
characters have the highest likelihood of interacting with during a time step.

"""

from collections import defaultdict
from typing import Any, Iterable, Iterator

import pydantic
from ordered_set import OrderedSet

from neighborly.ecs import Component, GameObject


class FrequentedBy(Component):
    """Tracks the characters that frequent a location."""

    __slots__ = ("_characters",)

    _characters: OrderedSet[GameObject]
    """GameObject IDs of characters that frequent the location."""

    def __init__(self) -> None:
        super().__init__()
        self._characters = OrderedSet([])

    def add_character(self, character: GameObject) -> None:
        """Add a character.

        Parameters
        ----------
        character
            The GameObject reference to a character.
        """
        self._characters.add(character)
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.frequented_by.{character.uid}"
        )

    def remove_character(self, character: GameObject) -> bool:
        """Remove a character.

        Parameters
        ----------
        character
            The character to remove.

        Returns
        -------
        bool
            Returns True if a character was removed. False otherwise.
        """
        if character in self._characters:
            self._characters.remove(character)
            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.frequented_by.{character.uid}"
            )
            return True

        return False

    def on_remove(self) -> None:
        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.frequented_by")

    def to_dict(self) -> dict[str, Any]:
        return {
            "characters": [entry.uid for entry in self._characters],
        }

    def __contains__(self, item: GameObject) -> bool:
        return item in self._characters

    def __iter__(self) -> Iterator[GameObject]:
        return iter(self._characters)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._characters})"


class FrequentedLocations(Component):
    """Tracks the locations that a character frequents."""

    __slots__ = ("_locations",)

    _locations: OrderedSet[GameObject]
    """A set of GameObject IDs of locations."""

    def __init__(self) -> None:
        super().__init__()
        self._locations = OrderedSet([])

    def add_location(self, location: GameObject) -> None:
        """Add a new location.

        Parameters
        ----------
        location
           A GameObject reference to a location.
        """
        self._locations.add(location)
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.frequented_locations.{location.uid}"
        )

    def remove_location(self, location: GameObject) -> bool:
        """Remove a location.

        Parameters
        ----------
        location
            A GameObject reference to a location to remove.

        Returns
        -------
        bool
            Returns True of a location was removed. False otherwise.
        """
        if location in self._locations:
            self._locations.remove(location)
            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.frequented_locations.{location.uid}"
            )
            return True
        return False

    def on_remove(self) -> None:
        self.gameobject.world.rp_db.delete(
            f"{self.gameobject.uid}.frequented_locations"
        )

    def to_dict(self) -> dict[str, Any]:
        return {"locations": [entry.uid for entry in self._locations]}

    def __contains__(self, item: GameObject) -> bool:
        return item in self._locations

    def __iter__(self) -> Iterator[GameObject]:
        return iter(self._locations)

    def __str__(self) -> str:
        return repr(self)

    def __len__(self) -> int:
        return len(self._locations)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self._locations)})"


class LocationPreferenceRule(pydantic.BaseModel):
    """A rule that helps characters score how they feel about locations to frequent."""

    rule_id: str
    """A unique ID for this rule."""
    preconditions: list[str]
    """Precondition functions to run when scoring a location."""
    probability: float
    """The amount to apply to the score."""


class LocationPreferences(Component):
    """A component that manages a character's location preference rules."""

    __slots__ = ("_rules",)

    _rules: defaultdict[str, int]
    """Rules IDs mapped to reference counts."""

    def __init__(self) -> None:
        super().__init__()
        self._rules = defaultdict(lambda: 0)

    @property
    def rules(self) -> Iterable[str]:
        """Rules applied to the owning GameObject's relationships."""
        return self._rules

    def add_rule(self, rule_id: str) -> None:
        """Add a rule to the rule collection."""
        self._rules[rule_id] += 1

    def has_rule(self, rule_id: str) -> bool:
        """Check if a rule is present."""
        return rule_id in self._rules

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the rules collection."""
        if rule_id in self._rules:
            self._rules[rule_id] -= 1

            if self._rules[rule_id] <= 0:
                del self._rules[rule_id]

            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        return {"rules": [r for r in self._rules]}
