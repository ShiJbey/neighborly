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
from typing import Any, ClassVar, Dict, Iterator, List, Optional, Protocol, Type

from ordered_set import OrderedSet

from neighborly.ecs import Component, GameObject, ISerializable, TagComponent, World
from neighborly.stats import Stat, StatModifier


class IncidenceModifierFn(Protocol):
    """A callable that calculates an optional modifier for a trait's incidence."""

    def __call__(self, gameobject: GameObject) -> Optional[StatModifier]:
        raise NotImplementedError()


class ITrait(TagComponent, ISerializable, ABC):
    """Additional state associated with characters, businesses, and other GameObjects.

    Users can use traits as another way to make runtime-changes to character behavior
    and component data. This class interface offers a more traditional object-oriented
    programming way of representing traits.

    Traits can apply and remove status effects using the component `on_add(...)` and
    `on_remove(...)` lifecycle methods.
    """

    base_incidence: ClassVar[float] = 0.0
    incidence_modifiers: ClassVar[List[IncidenceModifierFn]] = []

    @classmethod
    def get_incidence(cls, gameobject: GameObject) -> float:
        incidence_probability = Stat(base_value=cls.base_incidence)

        for modifier_fn in cls.incidence_modifiers:
            if modifier := modifier_fn(gameobject):
                incidence_probability.add_modifier(modifier)

        return incidence_probability.value

    @classmethod
    def on_register(cls, world: World) -> None:
        world.resource_manager.get_resource(TraitLibrary).add_trait_type(cls)

    def on_remove(self) -> None:
        self.gameobject.get_component(Traits).remove_trait(self)

    def on_add(self) -> None:
        self.gameobject.get_component(Traits).add_trait(self)


class Traits(Component):
    """Tracks the traits attached to a GameObject."""

    __slots__ = "_traits"

    _traits: OrderedSet[ITrait]
    """References to traits attached to the GameObject."""

    def __init__(self) -> None:
        super().__init__()
        self._traits = OrderedSet([])

    def add_trait(self, trait: ITrait) -> None:
        """Add a trait to the tracker.

        Parameters
        ----------
        trait
            A trait to add.
        """
        self._traits.add(trait)

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
        if trait in self._traits:
            self._traits.remove(trait)
            return True

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

    def __iter__(self) -> Iterator[Type[ITrait]]:
        return self._trait_types.values().__iter__()

    def __len__(self) -> int:
        return len(self._trait_types)
