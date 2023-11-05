"""Location Preference System.

This module contains classes and functions that help characters decide where within the
settlement they spend most of their time. Since the simulation does not model
characters' positions throughout the settlement, this is a way of tracking who
characters have the highest likelihood of interacting with during a time step.

"""

from typing import Any, Iterator

import attrs
from ordered_set import OrderedSet

from neighborly.ecs import Component, GameObject
from neighborly.preconditions.base_types import Precondition


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
            return True

        return False

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
            return True
        return False

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


@attrs.define
class LocationPreferenceRule:
    """A rule that helps characters score how they feel about locations to frequent."""

    preconditions: list[Precondition]
    """Precondition functions to run when scoring a location."""
    probability: float
    """The amount to apply to the score."""
    source: object
    """The source of this location."""

    def __call__(self, gameobject: GameObject) -> float:
        """Check all preconditions and return a weight modifier.

        Parameters
        ----------
        gameobject
            A location to score.

        Returns
        -------
        float
            A probability score from [0.0, 1.0] of the character frequenting the
            location. Or -1 if it does not pass the preconditions.
        """

        if all(p(gameobject) for p in self.preconditions):
            return self.probability

        return -1.0


class LocationPreferences(Component):
    """A component that manages a character's location preference rules."""

    __slots__ = ("_rules",)

    _rules: list[LocationPreferenceRule]
    """Rules added to the location preferences."""

    def __init__(self) -> None:
        super().__init__()
        self._rules = []

    def add_rule(self, rule: LocationPreferenceRule) -> None:
        """Add a location preference rule."""
        self._rules.append(rule)

    def remove_rule(self, rule: LocationPreferenceRule) -> None:
        """Remove a location preference rule."""
        self._rules.remove(rule)

    def remove_rules_from_source(self, source: object) -> None:
        """Remove all preference rules from the given source."""
        self._rules = [rule for rule in self._rules if rule.source != source]

    def score_location(self, location: GameObject) -> float:
        """Calculate a score for a character choosing to frequent this location.

        Parameters
        ----------
        location
            A location to score

        Returns
        -------
        float
            A probability score from [0.0, 1.0]
        """

        cumulative_score: float = 0.5
        consideration_count: int = 1

        for rule in self._rules:
            consideration_score = rule(location)

            # Scores greater than zero are added to the cumulative score
            if consideration_score > 0:
                cumulative_score += consideration_score
                consideration_count += 1

            # Scores equal to zero make the entire score zero (make zero a veto value)
            elif consideration_score == 0.0:
                cumulative_score = 0.0
                break

        # Scores are averaged using the arithmetic mean
        final_score = cumulative_score / consideration_count

        return final_score

    def to_dict(self) -> dict[str, Any]:
        return {}
