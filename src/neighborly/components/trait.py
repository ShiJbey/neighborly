"""Neighborly GameObject Traits.

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
)

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
    """

    @classmethod
    @abstractmethod
    def get_conflicts(cls) -> FrozenSet[Type[ITrait]]:
        """Get component types that this component's type conflicts with."""
        raise NotImplementedError


class Traits(Component):
    """Tracks the traits attached to the GameObject."""

    __slots__ = "_traits", "_traits_to_add", "_prohibited_traits"

    _traits: OrderedSet[ITrait]
    """A set of traits attached to the GameObject."""

    _prohibited_traits: Set[Type[ITrait]]
    """Trait types this GameObject cannot have based on its current traits."""

    _traits_to_add: OrderedSet[Type[ITrait]]
    """The types of traits to add to the GameObject."""

    def __init__(self, traits_to_add: Optional[Iterable[Type[ITrait]]] = None) -> None:
        super().__init__()
        self._traits = OrderedSet([])
        self._traits_to_add = OrderedSet(traits_to_add if traits_to_add else [])
        self._prohibited_traits = set()

    @property
    def prohibited_traits(self) -> Set[Type[ITrait]]:
        return self._prohibited_traits

    def on_add(self, gameobject: GameObject) -> None:
        """Construct the trait components and add them as traits."""
        for trait_type in self._traits_to_add:
            add_trait(
                gameobject=gameobject,
                trait=gameobject.world.gameobject_manager.create_component(trait_type),
            )

        self._traits_to_add.clear()

    def on_remove(self, gameobject: GameObject) -> None:
        """Remove all trait components."""
        for trait in self._traits:
            gameobject.remove_component(type(trait))

        self._traits.clear()

    def add_trait(self, trait: ITrait) -> None:
        """Add a trait to the tracker.

        Parameters
        ----------
        trait
            A trait to add.
        """
        if type(trait) not in self._prohibited_traits:
            self._traits.add(trait)
            self._prohibited_traits = self._prohibited_traits.union(
                trait.get_conflicts()
            )
        raise Exception(
            "Cannot add trait '{}' as it conflicts with existing traits.".format(
                type(trait).__name__
            )
        )

    def remove_trait(self, trait: ITrait) -> None:
        """Remove a trait from the tracker.

        Parameters
        ----------
        trait
            The trait to remove.
        """
        self._traits.remove(trait)
        self._prohibited_traits.clear()

        # Recalculate prohibited trait set
        for trait in self._traits:
            self._prohibited_traits = self._prohibited_traits.union(
                trait.get_conflicts()
            )

    def has_trait(self, trait: ITrait) -> bool:
        """Check if a GameObject has a trait.

        Parameters
        ----------
        trait
            The trait to check for.

        Returns
        -------
        bool
            True if the character has the trait, and false otherwise.
        """
        return trait in self._traits

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


class IHasRandomIncidence(ITrait, ABC):
    """Interface implemented by traits that can appear randomly at creation."""

    @classmethod
    @abstractmethod
    def incidence_probability(cls) -> float:
        """Get the probability of a trait appearing randomly at creation.

        Returns
        ------
        float
            A probability score from [0, 1.0]
        """
        return 0.5


class IInheritable(ITrait, ABC):
    """Interface implemented by traits passed genetically from parent(s) to children."""

    @classmethod
    @abstractmethod
    def inheritance_probability(cls) -> Tuple[float, float]:
        """Get the probability of a trait being inherited.

        Returns
        ------
        Tuple[float, float]
            The probability of a trait being inherited when one parent has it and when
            both parents have it, respectively.
        """
        return 0.5, 0.8


class TraitLibrary:
    """Manages information about Trait component types."""

    __slots__ = "_trait_types", "_incidental_traits"

    _trait_types: Dict[str, Type[ITrait]]
    """Trait types registered with the library"""

    _incidental_traits: OrderedSet[Type[IHasRandomIncidence]]
    """Trait types that may appear randomly"""

    def __init__(self) -> None:
        self._trait_types = {}
        self._incidental_traits = OrderedSet([])

    @property
    def incidental_traits(self) -> Iterable[Type[IHasRandomIncidence]]:
        return self._incidental_traits

    def add_trait_type(self, trait_type: Type[ITrait]) -> None:
        """Add a trait type."""
        self._trait_types[trait_type.__name__] = trait_type

        if issubclass(trait_type, IHasRandomIncidence):
            self._incidental_traits.add(trait_type)

    def get_trait_type(self, trait_name: str) -> Type[ITrait]:
        """Get a trait type by name."""
        return self._trait_types[trait_name]

    def __len__(self) -> int:
        return len(self._trait_types)


_TT = TypeVar("_TT", bound=ITrait)


def add_trait(gameobject: GameObject, trait: ITrait) -> None:
    """Add a trait to the given GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the trait to.
    trait
        The trait to add.
    """
    gameobject.get_component(Traits).add_trait(trait)
    gameobject.add_component(trait)


def get_trait(gameobject: GameObject, trait_type: Type[_TT]) -> _TT:
    """Get a trait from the given GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the trait to.
    trait_type
        The type trait of trait to retrieve.

    Returns
    -------
    Status
        The instance of the desired trait type.
    """
    return gameobject.get_component(trait_type)


def remove_trait(gameobject: GameObject, trait_type: Type[ITrait]) -> None:
    """Remove a trait from the given GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the trait to.
    trait_type
        The trait type to remove.
    """
    if trait := gameobject.try_component(trait_type):
        gameobject.get_component(Traits).remove_trait(trait)
        gameobject.remove_component(trait_type)


def has_trait(gameobject: GameObject, trait_type: Type[ITrait]) -> bool:
    """Check for a trait of a given type.

    Parameters
    ----------
    gameobject
        The GameObject to add the trait to.
    trait_type
        The trait type to remove.

    Returns
    -------
    bool
        True if the GameObject has a trait of the given type, False otherwise.
    """
    return gameobject.has_component(trait_type)


def register_trait(world: World, trait_type: Type[ITrait]) -> None:
    """Registers a trait component type with the world instance.

    Parameters
    ----------
    world
        The world instance
    trait_type
        The class of a trait component
    """
    world.gameobject_manager.register_component(trait_type)
    world.resource_manager.get_resource(TraitLibrary).add_trait_type(trait_type)
