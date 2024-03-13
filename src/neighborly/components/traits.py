"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from typing import Any, Iterable, Union

import attrs
from ordered_set import OrderedSet

from neighborly.defs.base_types import StatModifierData
from neighborly.ecs import Component
from neighborly.ecs.event import Event
from neighborly.ecs.game_object import GameObject


@attrs.define
class OnTraitAdded(Event):
    """Event emitted when a stat's value changes."""

    gameobject: GameObject
    trait: TraitInstance


@attrs.define
class OnTraitRemoved(Event):
    """Event emitted when a stat's value changes."""

    gameobject: GameObject
    trait: TraitInstance


class Trait(Component):
    """Additional state associated with characters, businesses, and other GameObjects.

    Users can use traits as another way to make runtime-changes to character behavior
    and component data. This class interface offers a more traditional object-oriented
    programming way of representing traits.

    This component is attached to a GameObject that represents a trait and should not
    be added directly to a character or business.
    """

    __slots__ = (
        "_definition_id",
        "_description",
        "_display_name",
        "_stat_modifiers",
        "_skill_modifiers",
        "_conflicting_traits",
    )

    _definition_id: str
    """The ID of this trait."""
    _description: str
    """A short description of the trait."""
    _display_name: str
    """The name of this trait."""
    _stat_modifiers: list[StatModifierData]
    """Stat modifiers to apply to GameObjects with this trait."""
    _skill_modifiers: list[StatModifierData]
    """Skill modifiers to apply to GameObjects with this trait."""
    _conflicting_traits: OrderedSet[str]
    """traits that this trait conflicts with."""

    def __init__(
        self,
        definition_id: str,
        display_name: str,
        description: str,
        stat_modifiers: list[StatModifierData],
        skill_modifiers: list[StatModifierData],
        conflicting_traits: Iterable[str],
    ) -> None:
        super().__init__()
        self._definition_id = definition_id
        self._display_name = display_name
        self._description = description
        self._stat_modifiers = stat_modifiers
        self._skill_modifiers = skill_modifiers
        self._conflicting_traits = OrderedSet(conflicting_traits)

    @property
    def definition_id(self) -> str:
        """The ID of this  trait."""
        return self._definition_id

    @property
    def display_name(self) -> str:
        """The name of this trait."""
        return self._display_name

    @property
    def description(self) -> str:
        """A short description of the trait."""
        return self._description

    @property
    def stat_modifiers(self) -> Iterable[StatModifierData]:
        """The data for initializing stat modifiers."""
        return self._stat_modifiers

    @property
    def skill_modifiers(self) -> Iterable[StatModifierData]:
        """The data for initializing skill stat modifiers."""
        return self._skill_modifiers

    @property
    def conflicting_traits(self) -> Iterable[str]:
        """A set of names of this trait's conflicts."""
        return self._conflicting_traits

    def __str__(self) -> str:
        return self.display_name

    def __repr__(self) -> str:
        return f"{type(self)}({self.definition_id!r})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "display_name": self.display_name,
            "description": self.description,
            "conflicts_with": list(self.conflicting_traits),
        }


class TraitInstance:
    """A record of a trait attached to a GameObject."""

    __slots__ = (
        "trait",
        "description",
        "has_duration",
        "duration",
        "data",
    )

    trait: Trait
    """The trait this is an instance of."""
    description: str
    """A description of the trait or the reason why it was applied."""
    has_duration: bool
    """Does this trait have a duration that needs to be ticked."""
    duration: int
    """Number of simulation ticks before this trait is removed."""
    data: dict[str, Any]
    """General key-value data store for the trait."""

    def __init__(self, trait: Trait, description: str, duration: int) -> None:
        self.trait = trait
        self.description = description
        self.has_duration = duration > 0
        self.duration = duration
        self.data = {}


class Traits(Component):
    """Tracks the traits attached to a GameObject."""

    __slots__ = ("_traits",)

    _traits: dict[str, TraitInstance]
    """Traits currently applied to the GameObject."""

    def __init__(self) -> None:
        super().__init__()
        self._traits = dict()

    @property
    def traits(self) -> Iterable[TraitInstance]:
        """Return an iterator for the trait collection."""
        return self._traits.values()

    def get_trait(self, trait: Union[str, Trait]) -> TraitInstance:
        """Get a trait instance."""
        if isinstance(trait, Trait):
            return self._traits[trait.definition_id]

        return self._traits[trait]

    def has_trait(self, trait: Union[str, Trait]) -> bool:
        """Check if a trait is present."""
        if isinstance(trait, Trait):
            return trait.definition_id in self._traits

        return trait in self._traits

    def add_trait(
        self, trait: Trait, duration: int = -1, description: str = ""
    ) -> bool:
        """Add a trait to the tracker.

        Parameters
        ----------
        trait
            A trait to add.
        duration
            The amount of time the trait will be active. (-1 is indefinite).
        description
            A description of the trait instance.

        Return
        ------
        bool
            True if the trait was added successfully, False if already present or
            if the trait conflict with existing traits.
        """

        if trait.definition_id in self._traits:
            return False

        if self.has_conflicting_trait(trait):
            return False

        self._traits[trait.definition_id] = TraitInstance(trait, description, duration)

        self.gameobject.world.events.dispatch_event(
            OnTraitAdded(
                gameobject=self.gameobject, trait=self._traits[trait.definition_id]
            )
        )
        return True

    def remove_trait(self, trait: Union[str, Trait]) -> bool:
        """Remove a trait from the tracker.

        Parameters
        ----------
        trait
            The trait to remove.

        Return
        ------
        bool
            True if a trait was successfully removed. False otherwise.
        """
        if isinstance(trait, Trait):
            if trait.definition_id not in self._traits:
                return False

            del self._traits[trait.definition_id]
            return True

        if trait not in self._traits:
            return False

        self.gameobject.world.events.dispatch_event(
            OnTraitRemoved(gameobject=self.gameobject, trait=self._traits[trait])
        )

        del self._traits[trait]
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
        for trait_instance in self._traits.values():
            if (
                trait.definition_id in trait_instance.trait.conflicting_traits
                or trait_instance.trait.definition_id in trait.definition_id
            ):
                return True

        return False

    def __str__(self) -> str:
        return f"{type(self).__name__}({list(self._traits)})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self._traits)})"

    def to_dict(self) -> dict[str, Any]:
        return {"traits": [t.trait.definition_id for t in self.traits]}
