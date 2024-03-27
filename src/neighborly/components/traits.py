"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Mapped, mapped_column

from neighborly.defs.base_types import TraitDef
from neighborly.ecs import Component, GameData, GameObject


class Trait(Component):
    """Marks a GameObject as being a TraitGameObject."""

    __slots__ = ("definition",)

    definition: TraitDef
    """This trait's definition."""

    def __init__(
        self,
        gameobject: GameObject,
        definition: TraitDef,
    ) -> None:
        super().__init__(gameobject)
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


class TraitInstance(GameData):
    """An instance of a trait being attached to a GameObject."""

    __tablename__ = "traits"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int]
    trait_id: Mapped[str]
    description: Mapped[str]
    has_duration: Mapped[bool]
    duration: Mapped[int]

    def __str__(self) -> str:
        return (
            f"Trait(trait={self.trait_id!r}, "
            f"duration={self.duration!r}, description={self.description!r})"
        )

    def __repr__(self) -> str:
        return (
            f"Trait(trait={self.trait_id!r}, "
            f"duration={self.duration!r}, description={self.description!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Return as serialized dict."""
        return {
            "trait": self.trait_id,
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
        self, trait_id: str, duration: int = -1, description: str = ""
    ) -> None:
        """Add a trait to the tracker.

        Parameters
        ----------
        trait
            A trait to add.
        """
        instance = TraitInstance(
            uid=self.gameobject.uid,
            trait_id=trait_id,
            description=description,
            has_duration=duration > 0,
            duration=duration,
        )

        self.traits[trait_id] = instance

        self.gameobject.world.rp_db.insert(f"{self.gameobject.uid}.traits.{trait_id}")

        with self.gameobject.world.session.begin() as session:
            session.add(instance)

    def remove_trait(self, trait_id: str) -> None:
        """Remove a trait from the tracker."""

        instance = self.traits[trait_id]

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.traits.{trait_id}")

        del self.traits[trait_id]

        with self.gameobject.world.session.begin() as session:
            session.delete(instance)

    def __str__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def __repr__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"instances": [t.to_dict() for t in self.traits.values()]}
