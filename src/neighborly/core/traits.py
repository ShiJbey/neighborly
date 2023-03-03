"""
traits.py

The simulation needs another way to handle personality representation aside from
virtues. Traits were supposed to be one of the additional ways that users could
add nuance to how characters treat each other what actions/events they engage in,
and where they choose to frequent within the settlement(s).
"""
from abc import ABC
from typing import Any, Dict, Iterator, List, Set, Type

from ordered_set import OrderedSet

from neighborly.core.ecs import Component


class TraitComponent(Component, ABC):
    """A specific trait held by a character"""

    excludes: Set[str] = set()

    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return f"TraitComponent::{self.__class__.__name__}"

    def __repr__(self) -> str:
        return f"TraitComponent::{self.__class__.__name__}"

    def to_dict(self) -> Dict[str, Any]:
        return {}


class TraitManager(Component):
    """Manages the state of statuses attached to the GameObject"""

    __slots__ = "_traits", "_prohibited_traits"

    def __init__(self) -> None:
        super().__init__()
        self._traits: OrderedSet[Type[TraitComponent]] = OrderedSet([])
        self._prohibited_traits: Dict[str, Set[str]] = {}

    def get_all(self) -> List[Type[TraitComponent]]:
        """Return all the statuses in the tracker"""
        return list(self._traits)

    def add(self, trait_type: Type[TraitComponent]) -> None:
        """Add a trait type to the tracker

        Parameters
        ----------
        trait_type: Type[Component]
            The trait type added to the GameObject
        """
        if trait_type.__name__ in self._prohibited_traits:
            raise RuntimeError(
                "Cannot add trait {} it conflicts with existing traits {}".format(
                    trait_type.__name__, self._prohibited_traits[trait_type.__name__]
                )
            )

        self._traits.add(trait_type)

        # Update the prohibited traits list and map the prohibited names
        # to the traits that prohibit them for debugging
        for trait_name in trait_type.excludes:
            if trait_name not in self._prohibited_traits:
                self._prohibited_traits[trait_name] = set()
            self._prohibited_traits[trait_name].add(trait_type.__name__)

    def has(self, trait_type: Type[TraitComponent]) -> bool:
        """Check if a trait type is active

        Parameters
        ----------
        trait_type: Type[Component]
            The trait type added to the GameObject

        Returns
        -------
        bool
            True if the trait is present
        """
        return trait_type in self

    def remove(self, trait_type: Type[TraitComponent]) -> None:
        """Remove a trait type from the tracker

        Parameters
        ----------
        trait_type: Type[Component]
            The trait type to be removed from the GameObject
        """
        self._traits.remove(trait_type)

        for trait_name in trait_type.excludes:
            if trait_name in self._prohibited_traits:
                self._prohibited_traits[trait_name].remove(trait_type.__name__)

                if len(self._prohibited_traits[trait_name]) == 0:
                    del self._prohibited_traits[trait_name]

    def clear(self) -> None:
        """Removes all statuses from the tracker gameobject"""
        self._traits.clear()
        self._prohibited_traits.clear()

    def __contains__(self, item: Type[TraitComponent]) -> bool:
        """Check if a trait type is attached to the GameObject"""
        return item in self._traits

    def __iter__(self) -> Iterator[Type[TraitComponent]]:
        """Return iterator to active trait types"""
        return self._traits.__iter__()

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._traits)

    def to_dict(self) -> Dict[str, Any]:
        return {"traits": [t.__name__ for t in self._traits]}
