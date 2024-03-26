"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neighborly.defs.base_types import TraitDef
from neighborly.ecs import Component


class Trait(Component):
    """Marks a GameObject as being a TraitGameObject."""

    __slots__ = ("definition",)

    definition: TraitDef
    """This trait's definition."""

    def __init__(
        self,
        definition: TraitDef,
    ) -> None:
        super().__init__()
        self.definition = definition

    @property
    def definition_id(self) -> str:
        """The definition ID of this trait."""
        return self.definition.definition_id

    def __str__(self) -> str:
        return f"Trait(definition={self.definition.definition_id!r})"

    def __repr__(self) -> str:
        return f"Trait(definition={self.definition.definition_id!r})"

    def to_dict(self) -> dict[str, Any]:
        return {}


@dataclass
class TraitInstance:
    """An instance of a trait being attached to a GameObject."""

    trait: Trait
    description: str
    has_duration: bool
    duration: int

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

    def __init__(self) -> None:
        super().__init__()
        self.traits = {}

    def add_trait(
        self, trait: Trait, duration: int = -1, description: str = ""
    ) -> bool:
        """Add a trait to the tracker.

        Parameters
        ----------
        trait
            A trait to add.

        Return
        ------
        bool
            True if the trait was added successfully, False if already present or
            if the trait conflict with existing traits.
        """

        if trait.definition_id in self.traits:
            return False

        if self.has_conflicting_trait(trait):
            return False

        self.traits[trait.definition_id] = TraitInstance(
            trait=trait,
            description=description if description else trait.definition.description,
            has_duration=duration > 0,
            duration=duration,
        )

        return True

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

            if instance.trait.definition_id in trait.definition.conflicts_with:
                return True

            if trait.definition_id in instance.trait.definition.conflicts_with:
                return True

        return False

    def __str__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def __repr__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"instances": [t.to_dict() for t in self.traits.values()]}
