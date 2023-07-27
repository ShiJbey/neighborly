"""Neighborly's Trait System.

Characters can have multiple traits applied to them that add modifiers to stats and
track component-specific data. Since traits are implemented as components, they are
eligible parameters when querying the simulation's world instance using
'world.get_components(...)'. Some traits can be passed from parents to children at
childbirth. We keep track of all traits attached to a character using a 'Traits' 
component.

"""

from __future__ import annotations

from abc import ABC
from typing import Any, Dict, FrozenSet, Iterator, Set, Tuple, Type

from ordered_set import OrderedSet

from neighborly.core.ecs import (
    Component,
    GameObject,
    ISerializable,
    TagComponent,
    World,
)


class ITrait(TagComponent, ISerializable, ABC):
    """Additional state associated with characters, businesses, and other GameObjects.

    Users can use traits as another way to make runtime-changes to character behavior
    and component data. This class interface offers a more traditional object-oriented
    programming way of representing traits.

    Traits can apply and remove status effects using the component `on_add(...)` and
    `on_remove(...)` lifecycle methods.
    """

    @classmethod
    def get_conflicts(cls) -> FrozenSet[Type[ITrait]]:
        """Get component types that this component's type conflicts with."""
        return frozenset()

    @classmethod
    def inheritance_probability(cls) -> Tuple[float, float]:
        """Get the probability of a trait being inherited.

        Returns
        ------
        Tuple[float, float]
            The probability of a trait being inherited when one parent has it and when
            both parents have it, respectively.
        """
        return 0.5, 0.8

    @classmethod
    def on_register(cls, world: World) -> None:
        world.resource_manager.get_resource(TraitLibrary).add_trait_type(cls)

    def on_remove(self, gameobject: GameObject) -> None:
        gameobject.get_component(Traits).remove_trait(self)

    def on_add(self, gameobject: GameObject) -> None:
        gameobject.get_component(Traits).add_trait(self)


class Traits(Component):
    """Tracks the traits attached to a GameObject."""

    __slots__ = "_traits", "_prohibited_traits"

    _traits: OrderedSet[ITrait]
    """References to traits attached to the GameObject."""

    _prohibited_traits: Set[Type[ITrait]]
    """Trait types this GameObject cannot have based on its current traits."""

    def __init__(self) -> None:
        super().__init__()
        self._traits = OrderedSet([])
        self._prohibited_traits = set()

    @property
    def prohibited_traits(self) -> FrozenSet[Type[ITrait]]:
        """Get a frozen set of all prohibited Trait types."""
        return frozenset(self._prohibited_traits)

    def add_trait(self, trait: ITrait) -> None:
        """Add a trait to the tracker.

        Parameters
        ----------
        trait
            A trait to add.
        """
        if type(trait) in self._prohibited_traits:
            raise Exception(
                "Cannot add trait '{}' as it conflicts with existing traits.".format(
                    type(trait).__name__
                )
            )

        self._traits.add(trait)
        self._prohibited_traits = self._prohibited_traits.union(trait.get_conflicts())

    def remove_trait(self, trait: ITrait) -> bool:
        """Remove a trait from the tracker.

        Parameters
        ----------
        trait
            The trait to remove.

        Return
        ------
        bool
            True if a trait was removed, False otherwise.
        """
        try:
            self._traits.remove(trait)
            self._prohibited_traits.clear()

            # Recalculate prohibited trait set
            for trait in self._traits:
                self._prohibited_traits = self._prohibited_traits.union(
                    trait.get_conflicts()
                )

            return True
        except ValueError:
            return False

    def iter_traits(self) -> Iterator[ITrait]:
        """Return an iterator for the trait collection."""
        return self._traits.__iter__()

    def __str__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__, [type(t).__name__ for t in self._traits]
        )

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__, [type(t).__name__ for t in self._traits]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"trait": [type(t).__name__ for t in self._traits]}


class TraitLibrary:
    """Manages information about Trait component types."""

    __slots__ = "_trait_types"

    _trait_types: Dict[str, Type[ITrait]]
    """Trait types registered with the library"""

    def __init__(self) -> None:
        self._trait_types = {}

    def add_trait_type(self, trait_type: Type[ITrait]) -> None:
        """Add a trait type."""
        self._trait_types[trait_type.__name__] = trait_type

    def get_trait_type(self, trait_name: str) -> Type[ITrait]:
        """Get a trait type by name."""
        return self._trait_types[trait_name]

    def __len__(self) -> int:
        return len(self._trait_types)
