"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from neighborly.ecs import Component, GameData, GameObject


class TraitInstance(GameData):
    """An instance of a trait being attached to a GameObject."""

    __tablename__ = "traits"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
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
        trait_id
            A ID of the trait to add.
        duration
            How long to add the trait.
        description
            A string description to about the trait.
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

    def tick_traits(self) -> None:
        """Tick the durations for the trait instances."""

        traits_to_remove: list[str] = []

        with self.gameobject.world.session.begin() as session:

            for trait_instance in self.traits.values():
                if not trait_instance.has_duration:
                    continue

                trait_instance.duration -= 1

                if trait_instance.duration <= 0:
                    session.delete(trait_instance)
                    traits_to_remove.append(trait_instance.trait_id)
                else:
                    session.add(trait_instance)

        for trait_id in traits_to_remove:
            self.remove_trait(trait_id)

    def __str__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def __repr__(self) -> str:
        return f"Traits(traits={list(self.traits.keys())!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"instances": [t.to_dict() for t in self.traits.values()]}
