"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from typing import Any, Iterable

from ordered_set import OrderedSet

from neighborly.ecs import Component, GameObject
from neighborly.effects.base_types import Effect


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
        "_effects",
        "_conflicting_traits",
    )

    _definition_id: str
    """The ID of this tag definition."""
    _description: str
    """A short description of the tag."""
    _display_name: str
    """The name of this tag printed."""
    _effects: list[Effect]
    """Effects to apply when the tag is added."""
    _conflicting_traits: OrderedSet[str]
    """traits that this trait conflicts with."""

    def __init__(
        self,
        definition_id: str,
        display_name: str,
        description: str,
        effects: list[Effect],
        conflicting_traits: Iterable[str],
    ) -> None:
        super().__init__()
        self._definition_id = definition_id
        self._display_name = display_name
        self._description = description
        self._effects = effects
        self._conflicting_traits = OrderedSet(conflicting_traits)

    @property
    def definition_id(self) -> str:
        """The ID of this tag definition."""
        return self._definition_id

    @property
    def display_name(self) -> str:
        """The name of this tag printed."""
        return self._display_name

    @property
    def description(self) -> str:
        """A short description of the tag."""
        return self._description

    @property
    def effects(self) -> Iterable[Effect]:
        """The effects associated with the trait."""
        return self._effects

    @property
    def conflicting_traits(self) -> Iterable[str]:
        """A set of names of this trait's conflicts."""
        return self._conflicting_traits

    def apply(self, target: GameObject) -> None:
        """Callback method executed when the trait is added.

        Parameters
        ----------
        target
            The gameobject with the trait
        """
        for effect in self._effects:
            effect.apply(target)

    def remove(self, target: GameObject) -> None:
        """Callback method executed when the trait is removed.

        Parameters
        ----------
        target
            The gameobject with the trait
        """
        for effect in self._effects:
            effect.remove(target)

    def __str__(self) -> str:
        return self.display_name

    def __repr__(self) -> str:
        return f"{type(self)}({self.definition_id})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "display_name": self.display_name,
            "description": self.description,
            "conflicts_with": list(self.conflicting_traits),
        }


class Traits(Component):
    """Tracks the traits attached to a GameObject."""

    __slots__ = "_traits", "_conflicting_traits"

    _traits: OrderedSet[GameObject]
    """References to traits attached to the GameObject."""
    _conflicting_traits: set[str]
    """IDs of all traits that conflict with the equipped traits."""

    def __init__(self) -> None:
        super().__init__()
        self._traits = OrderedSet([])
        self._conflicting_traits = set()

    @property
    def traits(self) -> Iterable[GameObject]:
        """Return an iterator for the trait collection."""
        return self._traits

    def has_trait(self, trait: GameObject) -> bool:
        """Check if a trait is present."""
        return trait in self._traits

    def add_trait(self, trait: GameObject) -> bool:
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

        if trait in self._traits:
            return False

        if self.has_conflicting_trait(trait):
            return False

        self._traits.add(trait)
        self._conflicting_traits = self._conflicting_traits.union(
            trait.get_component(Trait).conflicting_traits
        )
        trait.get_component(Trait).apply(self.gameobject)
        return True

    def remove_trait(self, trait: GameObject) -> bool:
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
        if trait in self._traits:
            self._traits.remove(trait)

            self._conflicting_traits = set()
            for remaining_trait in self._traits:
                self._conflicting_traits = self._conflicting_traits.union(
                    remaining_trait.get_component(Trait).conflicting_traits
                )

            trait.get_component(Trait).remove(self.gameobject)

            return True

        return False

    def has_conflicting_trait(self, trait: GameObject) -> bool:
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
        if trait.get_component(Trait).definition_id in self._conflicting_traits:
            return True

        incoming_trait_conflicts = trait.get_component(Trait).conflicting_traits

        return any(
            t.get_component(Trait).definition_id in incoming_trait_conflicts
            for t in self._traits
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}({list(self._traits)})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self._traits)})"

    def to_dict(self) -> dict[str, Any]:
        return {"traits": [t.uid for t in self._traits]}
