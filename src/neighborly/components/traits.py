"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

import enum
from typing import Any, Union

import attrs

from neighborly.datetime import SimDate
from neighborly.ecs import Component
from neighborly.effects.base_types import Effect


class TraitType(enum.Enum):
    """Enumeration of all possible trait types."""

    AGENT = enum.auto()
    RELATIONSHIP = enum.auto()


@attrs.define
class Trait:
    """Additional state associated with characters, businesses, and other GameObjects."""

    definition_id: str
    """The ID of this tag definition."""
    description: str
    """A short description of the tag."""
    name: str
    """The name of this tag printed."""
    trait_type: TraitType
    """The kind of GameObject the trait can attach to."""
    effects: list[Effect]
    """Effects to apply when the tag is added."""
    conflicting_traits: set[str]
    """traits that this trait conflicts with."""
    spawn_frequency: int = 0
    """(Agents only) The relative frequency of an agent spawning with this trait."""
    is_inheritable: bool = False
    """(Agents only) Is the trait inheritable."""
    inheritance_chance_single: float = 0.0
    """(Agents only) The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float = 0.0
    """(Agents only) The probability of inheriting this trait if both parents have it."""

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{type(self)}({self.definition_id})"


class TraitInstance:
    """An instance of a trait being attached to a GameObject."""

    __slots__ = ("trait", "duration", "has_duration", "timestamp")

    trait: Trait
    """The trait attached to the GameObject."""
    duration: int
    """The remaining number of time steps this trait is active for."""
    has_duration: bool
    """Does the trait have a duration time."""
    timestamp: SimDate
    """When was this trait acquired."""

    def __init__(self, trait: Trait, timestamp: SimDate, duration: int = 0) -> None:
        self.trait = trait
        self.has_duration = duration > 0
        self.duration = duration
        self.timestamp = timestamp

    def __str__(self) -> str:
        return (
            f"TraitInstance(trait={self.trait.definition_id!r}, "
            f"duration={self.duration!r}, "
            f"timestamp={self.timestamp})"
        )

    def __repr__(self) -> str:
        return (
            f"TraitInstance(trait={self.trait.definition_id!r}, "
            f"duration={self.duration!r}, "
            f"timestamp={self.timestamp})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return as serialized dict."""
        return {
            "trait": self.trait.definition_id,
            "has_duration": self.has_duration,
            "duration": self.duration,
            "timestamp": self.timestamp.to_iso_str(),
        }


class Traits(Component):
    """Tracks the traits attached to a GameObject."""

    __slots__ = ("traits",)

    traits: dict[str, TraitInstance]
    """References to traits attached to the GameObject."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.traits = {}

    def add_trait(self, trait: Trait, duration: int = -1) -> bool:
        """Add a trait to the tracker.

        Parameters
        ----------
        trait
            The trait to add.
        duration
            How long to add the trait.

        Returns
        -------
        bool
            True if successful; False otherwise.
        """
        if trait.definition_id in self.traits:
            return False

        if self.has_conflicting_trait(trait):
            return False

        instance = TraitInstance(
            trait=trait,
            timestamp=self.gameobject.world.resources.get_resource(SimDate).copy(),
            duration=duration,
        )

        self.traits[instance.trait.definition_id] = instance

        return True

    def remove_trait(self, trait: Trait) -> bool:
        """Remove a trait from the tracker."""

        if trait.definition_id in self.traits:

            del self.traits[trait.definition_id]

            return True

        return False

    def has_trait(self, trait: Union[str, Trait]) -> bool:
        """Check if the GameObject has a given trait."""
        if isinstance(trait, str):
            return trait in self.traits

        return trait.definition_id in self.traits

    def has_conflicting_trait(self, trait: Trait) -> bool:
        """Check if a trait conflicts with current traits.

        Parameters
        ----------
        trait
            The trait to check.

        Returns
        -------
        bool
            True if the trait conflicts with any of the current traits or if any current
            traits conflict with the given trait. False otherwise.
        """
        for instance in self.traits.values():

            if instance.trait.definition_id in trait.conflicting_traits:
                return True

            if trait.definition_id in instance.trait.conflicting_traits:
                return True

        return False

    def __str__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def __repr__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"instances": [t.to_dict() for t in self.traits.values()]}
