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


class Location(Component):
    """Tracks the characters that frequent a location."""

    __slots__ = (
        "is_private",
        "frequented_by",
    )

    is_private: bool
    """Private locations are not available to frequent except by certain characters."""
    frequented_by: OrderedSet[GameObject]
    """GameObject IDs of characters that frequent the location."""

    def __init__(self, is_private: bool) -> None:
        super().__init__()
        self.is_private = is_private
        self.frequented_by = OrderedSet([])

    def add_character(self, character: GameObject) -> None:
        """Add a character.

        Parameters
        ----------
        character
            The GameObject reference to a character.
        """
        self.frequented_by.add(character)

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
        if character in self.frequented_by:
            self.frequented_by.remove(character)
            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_private": self.is_private,
            "characters": [entry.uid for entry in self.frequented_by],
        }

    def __contains__(self, item: GameObject) -> bool:
        return item in self.frequented_by

    def __iter__(self) -> Iterator[GameObject]:
        return iter(self.frequented_by)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.frequented_by})"


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

    preconditions: list[str]
    """Precondition statements to run when scoring a location."""
    score: float
    """The amount to apply to the score."""

    def check_preconditions(self, gameobject: GameObject) -> float:
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

        raise NotImplementedError()
