"""Location Preference System.

This module contains classes and functions that help characters decide where within the
settlement they spend most of their time. Since the simulation does not model
characters' positions throughout the settlement, this is a way of tracking who
characters have the highest likelihood of interacting with during a time step.

"""

from typing import Any, Iterator, Optional

from ordered_set import OrderedSet

from neighborly.components.stats import StatModifierType
from neighborly.ecs import Component, GameObject
from neighborly.preconditions.base_types import Precondition


class Location(Component):
    """Tracks the characters that frequent a location."""

    __slots__ = ("frequented_by", "is_private")

    is_private: bool
    """Can this location be frequented by any character."""
    frequented_by: OrderedSet[GameObject]
    """GameObject IDs of characters that frequent the location."""

    def __init__(
        self,
        is_private: bool = False,
    ) -> None:
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
            "frequented_by": [entry.uid for entry in self.frequented_by],
        }

    def __contains__(self, item: GameObject) -> bool:
        return item in self.frequented_by

    def __iter__(self) -> Iterator[GameObject]:
        return iter(self.frequented_by)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"Location({self.frequented_by!r})"


class FrequentedLocations(Component):
    """Tracks the locations that a character frequents."""

    __slots__ = ("_locations",)

    _locations: OrderedSet[GameObject]
    """A set of GameObject IDs of locations."""

    def __init__(
        self,
    ) -> None:
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


class LocationPreference:
    """A rule that helps characters score how they feel about locations to frequent."""

    __slots__ = (
        "location_preconditions",
        "character_preconditions",
        "value",
        "modifier_type",
        "reason",
        "source",
    )

    location_preconditions: list[Precondition]
    """Precondition to run against the location when scoring."""
    character_preconditions: list[Precondition]
    """Precondition to run against a character when scoring."""
    value: float
    """The amount to apply to the score."""
    modifier_type: StatModifierType
    """How to apply the modifier value."""
    reason: str
    """The reason for this preference."""
    source: Optional[object]
    """The source of this preference."""

    def __init__(
        self,
        location_preconditions: list[Precondition],
        character_preconditions: list[Precondition],
        value: float,
        modifier_type: StatModifierType,
        reason: str = "",
        source: Optional[object] = None,
    ) -> None:
        self.location_preconditions = location_preconditions
        self.character_preconditions = character_preconditions
        self.value = value
        self.modifier_type = modifier_type
        self.reason = reason
        self.source = source

    def get_description(self) -> str:
        """Get a description of what the modifier does."""

        location_precondition_descriptions = "; ".join(
            [p.description for p in self.location_preconditions]
        )

        character_precondition_descriptions = "; ".join(
            [p.description for p in self.character_preconditions]
        )

        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        value_str = str(abs(self.value * 100)) if percent_sign else str(abs(self.value))

        return (
            f"Effect(s): Location preference {sign}{value_str}{percent_sign}\n"
            f"Location Precondition(s): {location_precondition_descriptions}\n"
            f"Character Precondition(s): {character_precondition_descriptions}\n"
            f"Reason: {self.reason}"
        )


class LocationPreferences(Component):
    """A component that manages a character's location preferences."""

    preferences: list[LocationPreference]
    """All location preference modifiers."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.preferences = []

    def add_preference(self, preference: LocationPreference) -> None:
        """Add a preference to the manager."""
        self.preferences.append(preference)

    def remove_preference(self, preference: LocationPreference) -> bool:
        """Remove a preference from the manager.

        Returns
        -------
        bool
            True if successfully removed.
        """
        try:
            self.preferences.remove(preference)
            return True
        except ValueError:
            return False

    def remove_from_source(self, source: object) -> bool:
        """Remove all preferences from a given source.

        Returns
        -------
        bool
            True if successfully removed.
        """
        any_preference_removed = False

        for i in reversed(range(len(self.preferences))):
            if self.preferences[i].source == source:
                self.preferences.pop(i)
                any_preference_removed = True

        return any_preference_removed

    def to_dict(self) -> dict[str, Any]:
        return {}


class CurrentSettlement(Component):
    """Tracks the current settlement a GameObject is in."""

    __slots__ = ("settlement",)

    settlement: GameObject

    def __init__(self, settlement: GameObject) -> None:
        super().__init__()
        self.settlement = settlement

    def to_dict(self) -> dict[str, Any]:
        return {"settlement": self.settlement.uid}


class CurrentDistrict(Component):
    """Tracks the current district a GameObject is in."""

    __slots__ = ("district",)

    district: GameObject

    def __init__(self, district: GameObject) -> None:
        super().__init__()
        self.district = district

    def to_dict(self) -> dict[str, Any]:
        return {"district": self.district.uid}
