from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Type, TypeVar, Union

from neighborly.core.ecs import Component, GameObject


@dataclass()
class InheritableComponentInfo:
    """
    Fields
    ------
    inheritance_chance: Tuple[float, float]
        Probability that a character inherits a component when only on parent has
        it and the probability if both characters have it
    always_inherited: bool
        Indicates that a component should be inherited regardless of
    """

    inheritance_chance: Tuple[float, float]
    always_inherited: bool
    requires_both_parents: bool


_inheritable_components: Dict[Type[Component], InheritableComponentInfo] = {}


class IInheritable(ABC):
    @classmethod
    @abstractmethod
    def from_parents(
        cls, parent_a: Optional[Component], parent_b: Optional[Component]
    ) -> Component:
        """Build a new instance of the component using instances from the parents"""
        raise NotImplementedError


_CT = TypeVar("_CT", bound="Component")


def inheritable(
    requires_both_parents: bool = False,
    inheritance_chance: Union[int, Tuple[float, float]] = (0.5, 0.5),
    always_inherited: bool = False,
):
    """Class decorator for components that can be inherited from characters' parents"""

    def wrapped(cls: Type[_CT]) -> Type[_CT]:
        if not callable(getattr(cls, "from_parents", None)):
            raise RuntimeError("Component does not implement IInheritable interface.")

        _inheritable_components[cls] = InheritableComponentInfo(
            requires_both_parents=requires_both_parents,
            inheritance_chance=(
                inheritance_chance
                if type(inheritance_chance) == tuple
                else (inheritance_chance, inheritance_chance)
            ),
            always_inherited=always_inherited,
        )
        return cls

    return wrapped


def is_inheritable(component_type: Type[Component]) -> bool:
    """Returns True if a component is inheritable from parent to child"""
    return component_type in _inheritable_components


def get_inheritable_components(gameobject: GameObject) -> List[Type[Component]]:
    """Returns all the component type associated with the GameObject that are inheritable"""
    inheritable_components = list()
    # Get inheritable components from parent_a
    for component_type in gameobject.get_component_types():
        if is_inheritable(component_type):
            inheritable_components.append(component_type)
    return inheritable_components


def get_inheritable_traits_given_parents(
    parent_a: GameObject, parent_b: GameObject
) -> Tuple[List[Type[Component]], List[Tuple[float, Type[Component]]]]:
    """
    Returns a
    Parameters
    ----------
    parent_a
    parent_b

    Returns
    -------
    List[Type[Component]]
        The component types that can be inherited from
    """

    parent_a_inheritables = set(get_inheritable_components(parent_a))

    parent_b_inheritables = set(get_inheritable_components(parent_b))

    shared_inheritables = parent_a_inheritables.intersection(parent_b_inheritables)

    all_inheritables = parent_a_inheritables.union(parent_b_inheritables)

    required_components = []
    random_pool = []

    for component_type in all_inheritables:
        if _inheritable_components[component_type].always_inherited:
            required_components.append(component_type)
            continue

        if _inheritable_components[component_type].requires_both_parents:
            if component_type in shared_inheritables:
                required_components.append(component_type)
                continue

        if component_type in shared_inheritables:
            random_pool.append(
                (
                    _inheritable_components[component_type].inheritance_chance[1],
                    component_type,
                )
            )
        else:
            random_pool.append(
                (
                    _inheritable_components[component_type].inheritance_chance[0],
                    component_type,
                )
            )

    return required_components, random_pool
