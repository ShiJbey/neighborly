"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import ForeignKey, delete
from sqlalchemy.orm import Mapped, mapped_column

from neighborly.ecs import Component, GameData, GameObject
from neighborly.effects.base_types import Effect


class Trait:
    """Additional state associated with characters, businesses, and other GameObjects."""

    __slots__ = (
        "definition_id",
        "description",
        "name",
        "effects",
        "conflicting_traits",
    )

    definition_id: str
    """The ID of this tag definition."""
    description: str
    """A short description of the tag."""
    name: str
    """The name of this tag printed."""
    effects: list[Effect]
    """Effects to apply when the tag is added."""
    conflicting_traits: set[str]
    """traits that this trait conflicts with."""

    def __init__(
        self,
        definition_id: str,
        name: str,
        description: str,
        effects: list[Effect],
        conflicting_traits: Iterable[str],
    ) -> None:
        self.definition_id = definition_id
        self.name = name
        self.description = description
        self.effects = effects
        self.conflicting_traits = set(conflicting_traits)

    def apply_effects(self, target: GameObject) -> None:
        """Callback method executed when the trait is added.

        Parameters
        ----------
        target
            The gameobject with the trait
        """
        for effect in self.effects:
            effect.apply(target)

    def remove_effects(self, target: GameObject) -> None:
        """Callback method executed when the trait is removed.

        Parameters
        ----------
        target
            The gameobject with the trait
        """
        for effect in self.effects:
            effect.remove(target)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{type(self)}({self.definition_id})"


class TraitInstanceData(GameData):
    """An instance of a trait being attached to a GameObject."""

    __tablename__ = "traits"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    trait_id: Mapped[str]

    def __str__(self) -> str:
        return f"TraitInstanceData(uid={self.uid}, trait={self.trait_id!r})"

    def __repr__(self) -> str:
        return f"TraitInstanceData(uid={self.uid}, trait={self.trait_id!r})"


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

        # Add the trait to the SQL database
        with self.gameobject.world.session.begin() as session:
            session.add(
                TraitInstanceData(uid=self.gameobject.uid, trait_id=trait.definition_id)
            )

        # Apply the effects of the trait
        trait.apply_effects(self.gameobject)

        return True

    def remove_trait(self, trait: Trait) -> bool:
        """Remove a trait from the tracker."""

        if trait.definition_id in self.traits:

            del self.traits[trait.definition_id]

            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.traits.{trait.definition_id}"
            )

            with self.gameobject.world.session.begin() as session:
                session.execute(
                    delete(TraitInstanceData)
                    .where(TraitInstanceData.uid == self.gameobject.uid)
                    .where(TraitInstanceData.trait_id == trait.definition_id)
                )

            trait.remove_effects(self.gameobject)

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

    def tick_traits(self) -> None:
        """Tick the durations for the trait instances."""

        traits_to_remove: list[Trait] = []

        with self.gameobject.world.session.begin() as session:

            for trait_instance in self.traits.values():
                if not trait_instance.has_duration:
                    continue

                trait_instance.duration -= 1

                if trait_instance.duration <= 0:
                    session.delete(trait_instance)
                    traits_to_remove.append(trait_instance.trait)
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
