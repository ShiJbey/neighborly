"""Neighborly ECS World Implementation.

"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Type, TypeVar, Union, overload

from neighborly.ecs.event import EventManager
from neighborly.ecs.game_object import GameObjectManager
from neighborly.ecs.resources import ResourceManager
from neighborly.ecs.system import SystemManager

if TYPE_CHECKING:
    from neighborly.ecs.component import Component

_T1 = TypeVar("_T1", bound="Component")
_T2 = TypeVar("_T2", bound="Component")
_T3 = TypeVar("_T3", bound="Component")
_T4 = TypeVar("_T4", bound="Component")
_T5 = TypeVar("_T5", bound="Component")
_T6 = TypeVar("_T6", bound="Component")
_T7 = TypeVar("_T7", bound="Component")
_T8 = TypeVar("_T8", bound="Component")


class World:
    """Manages Gameobjects, Systems, events, and resources."""

    __slots__ = (
        "_rng",
        "_resource_manager",
        "_gameobject_manager",
        "_system_manager",
        "_event_manager",
    )

    _rng: random.Random
    """Random number generator"""
    _gameobject_manager: GameObjectManager
    """Manages GameObjects and Component data."""
    _resource_manager: ResourceManager
    """Global resources shared by systems in the ECS."""
    _system_manager: SystemManager
    """The systems run every simulation step."""
    _event_manager: EventManager
    """Manages event listeners."""

    def __init__(self) -> None:
        self._rng = random.Random()
        self._resource_manager = ResourceManager()
        self._system_manager = SystemManager(self)
        self._event_manager = EventManager()
        self._gameobject_manager = GameObjectManager(self)

    @property
    def systems(self) -> SystemManager:
        """The world's system manager."""
        return self._system_manager

    @property
    def gameobjects(self) -> GameObjectManager:
        """The world's gameobject manager"""
        return self._gameobject_manager

    @property
    def resources(self) -> ResourceManager:
        """The world's resource manager"""
        return self._resource_manager

    @property
    def events(self) -> EventManager:
        """The world's event manager."""
        return self._event_manager

    @property
    def rng(self) -> random.Random:
        """The world's random number generator."""
        return self._rng

    def get_component(self, component_type: Type[_T1]) -> list[tuple[int, _T1]]:
        """Get all the GameObjects that have a given component type.

        Parameters
        ----------
        component_type
            The component type to check for.

        Returns
        -------
        list[tuple[int, _CT]]
            A list of tuples containing the ID of a GameObject and its respective
            component instance.
        """
        return self._gameobject_manager.component_manager.get_component(  # type: ignore
            component_type
        )

    @overload
    def get_components(
        self, component_types: tuple[Type[_T1]]
    ) -> list[tuple[int, tuple[_T1]]]: ...

    @overload
    def get_components(
        self, component_types: tuple[Type[_T1], Type[_T2]]
    ) -> list[tuple[int, tuple[_T1, _T2]]]: ...

    @overload
    def get_components(
        self, component_types: tuple[Type[_T1], Type[_T2], Type[_T3]]
    ) -> list[tuple[int, tuple[_T1, _T2, _T3]]]: ...

    @overload
    def get_components(
        self, component_types: tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4]]
    ) -> list[tuple[int, tuple[_T1, _T2, _T3, _T4]]]: ...

    @overload
    def get_components(
        self,
        component_types: tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5]],
    ) -> list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5]]]: ...

    @overload
    def get_components(
        self,
        component_types: tuple[
            Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6]
        ],
    ) -> list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6]]]: ...

    @overload
    def get_components(
        self,
        component_types: tuple[
            Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6], Type[_T7]
        ],
    ) -> list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]]: ...

    @overload
    def get_components(
        self,
        component_types: tuple[
            Type[_T1],
            Type[_T2],
            Type[_T3],
            Type[_T4],
            Type[_T5],
            Type[_T6],
            Type[_T7],
            Type[_T8],
        ],
    ) -> list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]]: ...

    def get_components(
        self,
        component_types: Union[
            tuple[Type[_T1]],
            tuple[Type[_T1], Type[_T2]],
            tuple[Type[_T1], Type[_T2], Type[_T3]],
            tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4]],
            tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5]],
            tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6]],
            tuple[
                Type[_T1],
                Type[_T2],
                Type[_T3],
                Type[_T4],
                Type[_T5],
                Type[_T6],
                Type[_T7],
            ],
            tuple[
                Type[_T1],
                Type[_T2],
                Type[_T3],
                Type[_T4],
                Type[_T5],
                Type[_T6],
                Type[_T7],
                Type[_T8],
            ],
        ],
    ) -> Union[
        list[tuple[int, tuple[_T1]]],
        list[tuple[int, tuple[_T1, _T2]]],
        list[tuple[int, tuple[_T1, _T2, _T3]]],
        list[tuple[int, tuple[_T1, _T2, _T3, _T4]]],
        list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5]]],
        list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6]]],
        list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]],
        list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]],
    ]:
        """Get all game objects with the given components.

        Parameters
        ----------
        component_types
            The components to check for

        Returns
        -------
        Union[
            list[tuple[int, tuple[_T1]]],
            list[tuple[int, tuple[_T1, _T2]]],
            list[tuple[int, tuple[_T1, _T2, _T3]]],
            list[tuple[int, tuple[_T1, _T2, _T3, _T4]]],
            list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5]]],
            list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6]]],
            list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]],
            list[tuple[int, tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]],
        ]
            list of tuples containing a GameObject ID and an additional tuple with
            the instances of the given component types, in-order.
        """
        ret = self._gameobject_manager.component_manager.get_components(
            *component_types
        )

        # We have to ignore the type because of esper's lax type hinting for
        # world.get_components()
        return ret  # type: ignore

    def step(self) -> None:
        """Advance the simulation as single tick and call all the systems."""
        self._gameobject_manager.clear_dead_gameobjects()
        self._system_manager.update_systems()
