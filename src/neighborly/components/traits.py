"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

import enum
from typing import Any, Iterable

from neighborly.ecs import Component, GameObject
from neighborly.effects.base_types import Effect


class TraitType(enum.Enum):
    """Enumeration of all possible trait types."""

    AGENT = enum.auto()
    RELATIONSHIP = enum.auto()


class Trait:
    """Additional state associated with characters, businesses, and other GameObjects."""

    __slots__ = (
        "definition_id",
        "description",
        "name",
        "trait_type",
        "effects",
        "conflicting_traits",
        "incoming_relationship_effects",
        "outgoing_relationship_effects",
        "owner_effects",
        "target_effects",
    )

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
    incoming_relationship_effects: list[Effect]
    """(Agents only) Effects to incoming relationships."""
    outgoing_relationship_effects: list[Effect]
    """(Agents only) Effects to outgoing relationships."""
    owner_effects: list[Effect]
    """(Relationships only) Effects to the owner of a relationship."""
    target_effects: list[Effect]
    """(Relationships only) Effects to the target of a relationship."""

    def __init__(
        self,
        definition_id: str,
        name: str,
        trait_type: TraitType,
        description: str,
        effects: list[Effect],
        incoming_relationship_effects: list[Effect],
        outgoing_relationship_effects: list[Effect],
        owner_effects: list[Effect],
        target_effects: list[Effect],
        conflicting_traits: Iterable[str],
    ) -> None:
        self.definition_id = definition_id
        self.name = name
        self.trait_type = trait_type
        self.description = description
        self.effects = effects
        self.conflicting_traits = set(conflicting_traits)
        self.incoming_relationship_effects = incoming_relationship_effects
        self.outgoing_relationship_effects = outgoing_relationship_effects
        self.owner_effects = owner_effects
        self.target_effects = target_effects

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{type(self)}({self.definition_id})"


class TraitInstance:
    """An instance of a trait being attached to a GameObject."""

    __slots__ = ("trait", "description", "duration", "has_duration")

    trait: Trait
    """The trait attached to the GameObject."""
    description: str
    """A description of the trait or why it was added."""
    duration: int
    """The remaining number of time steps this trait is active for."""
    has_duration: bool
    """Does the trait have a duration time."""

    def __init__(self, trait: Trait, description: str = "", duration: int = 0) -> None:
        self.trait = trait
        self.description = description
        self.has_duration = duration > 0
        self.duration = duration

    def __str__(self) -> str:
        return (
            f"Trait(trait={self.trait.definition_id!r}, "
            f"duration={self.duration!r}, description={self.description!r})"
        )

    def __repr__(self) -> str:
        return (
            f"Trait(trait={self.trait.definition_id!r}, "
            f"duration={self.duration!r}, description={self.description!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return as serialized dict."""
        return {
            "trait": self.trait.definition_id,
            "description": self.description,
            "has_duration": self.has_duration,
            "duration": self.duration,
        }


class Traits(Component):
    """Tracks the traits attached to a GameObject."""

    __slots__ = ("traits",)

    traits: dict[str, TraitInstance]
    """References to traits attached to the GameObject."""

    def __init__(
        self,
        gameobject: GameObject,
    ) -> None:
        super().__init__(gameobject)
        self.traits = {}

    def add_trait(
        self, trait: Trait, duration: int = -1, description: str = ""
    ) -> bool:
        """Add a trait to the tracker.

        Parameters
        ----------
        trait
            The trait to add.
        duration
            How long to add the trait.
        description
            A string description to about the trait.

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
            trait=trait, duration=duration, description=description
        )

        self.traits[instance.trait.definition_id] = instance

        # Add the trait to the repraxis database
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.traits.{trait.definition_id}"
        )

        return True

    def remove_trait(self, trait: Trait) -> bool:
        """Remove a trait from the tracker."""

        if trait.definition_id in self.traits:

            del self.traits[trait.definition_id]

            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.traits.{trait.definition_id}"
            )

            return True

        return False

    def has_trait(self, trait: Trait) -> bool:
        """Check if the GameObject has a given trait."""

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
