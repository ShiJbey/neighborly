"""
ecs.py

Custom Entity-Component implementation that blends the Unity-style GameObjects with the
ECS logic from the Python esper library and the Bevy Game Engine.

This ECS implementation is not thread-safe. It assumes that everything happens
sequentially on the same thread. There some features that were originally designed to
solve multithreading problems in Unity's Entities package. However, they are used here
more for adding reactivity.

Sources:

https://docs.unity3d.com/ScriptReference/GameObject.html

https://github.com/benmoran56/esper

https://github.com/bevyengine/bevy

https://bevy-cheatbook.github.io/programming/change-detection.html

https://bevy-cheatbook.github.io/programming/removal-detection.html

https://docs.unity3d.com/Packages/com.unity.entities@0.1/manual/index.html
"""
from __future__ import annotations

import dataclasses
import logging
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    Any,
    DefaultDict,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

import esper
import pydantic
from ordered_set import OrderedSet

logger = logging.getLogger(__name__)

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")
_ST = TypeVar("_ST", bound="ISystem")


class ResourceNotFoundError(Exception):
    """Exception raised when attempting to access a resource that does not exist

    Attributes
    ----------
    resource_type: Type[Any]
        The type of the resource
    message: str
        An error message
    """

    __slots__ = "resource_type", "message"

    def __init__(self, resource_type: Type[Any]) -> None:
        """
        Parameters
        ----------
        resource_type: Type[Any]
            The type of the resource not found
        """
        super().__init__()
        self.resource_type: Type[Any] = resource_type
        self.message = f"Could not find resource with type: {resource_type.__name__}"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(resource_type={})".format(
            self.__class__.__name__, self.resource_type
        )


class GameObjectNotFoundError(Exception):
    """Exception raised when attempting to retrieve a GameObject that does not exist

    Attributes
    ----------
    gameobject_uid: int
        The unique ID of the desired GameObject
    message: str
        An error message
    """

    __slots__ = "gameobject_uid", "message"

    def __init__(self, gameobject_uid: int) -> None:
        """
        Parameters
        ----------
        gameobject_uid: int
            The unique ID of the desired GameObject
        """
        super().__init__()
        self.gameobject_uid: int = gameobject_uid
        self.message = f"Could not find GameObject with id: {gameobject_uid}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(gameobject_uid={})".format(
            self.__class__.__name__, self.gameobject_uid
        )


class ComponentNotFoundError(Exception):
    """Exception raised when attempting to retrieve a component that does not exist

    Attributes
    ----------
    component_type: Type[Component]
        The type of component not found
    message: str
        An error message
    """

    __slots__ = "component_type", "message"

    def __init__(self, component_type: Type[Component]) -> None:
        """
        Parameters
        ----------
        component_type: Type[Component]
            The desired component type
        """
        super().__init__()
        self.component_type: Type[Component] = component_type
        self.message = "Could not find Component with type {}.".format(
            component_type.__name__
        )

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(component_type={})".format(
            self.__class__.__name__,
            self.component_type.__name__,
        )


class GameObject:
    """A reference to an entity within the world

    GameObjects wrap a unique integer identifier provide an interface to manipulate
    an entity, its components, and its hierarchical relationship with other entities.

    Attributes
    ----------
    name: str
        The name of the GameObject
    children: List[GameObject]
        Other GameObjects that are below this one in the hierarchy
        and are removed when this GameObject is removed
    parent: Optional[GameObject]
        The GameObject that this GameObject is a child of
    """

    __slots__ = "_id", "name", "_world", "children", "parent", "_is_active"

    def __init__(
        self,
        unique_id: int,
        world: World,
        name: str = "",
    ) -> None:
        """
        Parameters
        ----------
        unique_id: int
            A unique identifier
        world: World
            The world instance that this GameObject belongs to
        name: str, optional
            An optional name to give to the GameObject
            (Defaults to 'GameObject(<unique_id>)')
        """
        self.name: str = name if name else f"GameObject({unique_id})"
        self._id: int = unique_id
        self._world: World = world
        self.parent: Optional[GameObject] = None
        self.children: List[GameObject] = []
        self._is_active: bool = True

    @property
    def uid(self) -> int:
        """Return GameObject's ID"""
        return self._id

    @property
    def world(self) -> World:
        """Return the world that this GameObject belongs to"""
        return self._world

    @property
    def exists(self) -> bool:
        """Return True if the GameObject still exists in the ECS"""
        return self.world.has_gameobject(self._id)

    @property
    def is_active(self) -> bool:
        """Return if this GameObject is active and exists in the ECS"""
        return self._is_active and self.exists

    def set_active(self, is_active: bool) -> None:
        """Set the active status of the GameObject

        Parameters
        ----------
        is_active: bool
            desired active state
        """
        self._is_active = is_active

    def get_components(self) -> Tuple[Component, ...]:
        """Returns the component instances associated with this GameObject"""
        try:
            return self.world.get_components_for_entity(self.uid)
        except KeyError:
            # Ignore errors if gameobject is not found in esper ecs
            return ()

    def get_component_types(self) -> Tuple[Type[Component], ...]:
        """Returns the types of components attached to this character"""
        return tuple(map(lambda component: type(component), self.get_components()))

    def add_component(self, component: Component) -> None:
        """Add a component to this GameObject

        Parameters
        ----------
        component: Component
            An instance of a component

        Notes
        -----
        Adding components is an immediate operation.
        """
        self.world.add_component(self.uid, component)

    def remove_component(self, component_type: Type[Component]) -> None:
        """Remove a component from the GameObject

        Parameters
        ----------
        component_type: Type[Component]
            The type of the component to remove
        """
        self.world.remove_component(self.uid, component_type)

    def get_component(self, component_type: Type[_CT]) -> _CT:
        return self.world.get_component_for_entity(self.uid, component_type)

    def has_components(self, *component_types: Type[Component]) -> bool:
        return self.world.has_components(self.uid, *component_types)

    def has_component(self, component_type: Type[Component]) -> bool:
        """Check if this entity has a component of a given type"""
        return self.world.has_component(self.uid, component_type)

    def try_component(self, component_type: Type[_CT]) -> Optional[_CT]:
        try:
            return self.world.try_component_for_entity(self.uid, component_type)
        except KeyError:
            return None

    def add_child(self, gameobject: GameObject) -> None:
        """Add a GameObject as the child of this GameObject"""
        if gameobject.parent is not None:
            gameobject.parent.remove_child(gameobject)
        gameobject.parent = self
        self.children.append(gameobject)

    def remove_child(self, gameobject: GameObject) -> None:
        """Remove a GameObject as a child of this GameObject"""
        self.children.remove(gameobject)
        gameobject.parent = None

    def get_component_in_child(self, component_type: Type[_CT]) -> Tuple[int, _CT]:
        """Get a single instance of a component type attached to a child

        Performs a depth-first search of the children and their children and
        returns the first instance of the component type
        """

        stack: List[GameObject] = list(*self.children)
        checked: Set[GameObject] = set()

        while stack:
            entity = stack.pop()

            if entity in checked:
                continue

            checked.add(entity)

            if component := entity.try_component(component_type):
                return entity.uid, component

            for child in entity.children:
                stack.append(child)

        raise ComponentNotFoundError(component_type)

    def get_component_in_children(
        self, component_type: Type[_CT]
    ) -> List[Tuple[int, _CT]]:
        """Get all the instances of a component type attached to the immediate children of this GameObject"""
        results: List[Tuple[int, _CT]] = []

        stack: List[GameObject] = list(*self.children)
        checked: Set[GameObject] = set()

        while stack:
            entity = stack.pop()

            if entity in checked:
                continue

            checked.add(entity)

            if component := entity.try_component(component_type):
                results.append((entity.uid, component))

            for child in entity.children:
                stack.append(child)

        return results

    def destroy(self) -> None:
        """Remove the GameObject from its World instance"""
        self.world.delete_gameobject(self.uid)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the GameObject to a Dict"""
        ret = {
            "id": self.uid,
            "name": self.name,
            "parent": self.parent.uid if self.parent else -1,
            "children": [c.uid for c in self.children],
            "components": {
                c.__class__.__name__: c.to_dict() for c in self.get_components()
            },
        }

        return ret

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GameObject):
            return self.uid == other.uid
        raise TypeError(f"Expected GameObject but was {type(other)}")

    def __int__(self) -> int:
        return self._id

    def __hash__(self) -> int:
        return self._id

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return "{}(id={}, name={}, parent={}, children={})".format(
            self.__class__.__name__, self.uid, self.name, self.parent, self.children
        )


@dataclass(frozen=True)
class RemovedComponentPair(Generic[_CT]):
    guid: int
    component: _CT

    def __hash__(self) -> int:
        return self.guid


class Component(ABC):
    """Components are collections of related data attached to GameObjects"""

    __slots__ = "_gameobject"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._gameobject: Optional[GameObject] = None

    @property
    def gameobject(self) -> GameObject:
        """Return the GameObject this component is attached to"""
        if self._gameobject is None:
            raise TypeError("Component's GameObject is None")
        return self._gameobject

    def set_gameobject(self, gameobject: Optional[GameObject]) -> None:
        """
        Set the gameobject instance for this component

        Parameters
        ----------
        gameobject: Optional[GameObject]
            The GameObject instance or None if being removed from a GameObject
        """
        self._gameobject = gameobject

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the component to a dict"""
        raise NotImplementedError


class ISystem(ABC, esper.Processor):
    """Abstract base class implementation for ECS systems

    Class Attributes
    ----------------
    sys_group: str
        The system group this system belongs to
    run_after: str
        The system this system must run after
    world: World
        The world instance this system belongs to
    """

    sys_group: str = "root"

    # We have to re-type the 'world' class variable because
    # it is declared as 'Any' by esper, and we need it to
    # be of type World
    world: World  # type: ignore

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @classmethod
    def get_world(cls) -> World:
        """Get the system's world instance"""
        return cls.world


class SystemGroup(ISystem, ABC):
    """A group of simulation systems that run as a unit"""

    group_name: str = ""

    __slots__ = "_sub_systems"

    def __init__(self) -> None:
        super().__init__()
        self._sub_systems: List[ISystem] = []

    @classmethod
    def get_name(cls) -> str:
        """Get the name of the group"""
        return cls.group_name

    def iter_children(self) -> Iterator[ISystem]:
        """Return an iterator for the groups children"""
        return self._sub_systems.__iter__()

    def add_child(self, sub_system: ISystem) -> None:
        """Add a new system as a sub_system of this group

        Parameters
        ----------
        sub_system: ISystem
            The system to add to this group
        """
        self._sub_systems.append(sub_system)
        self._sub_systems.sort(key=lambda s: s.priority, reverse=True)

    def remove_child(self, sub_system_type: Type[ISystem]) -> None:
        """Remove children of the given type"""
        children_to_remove = [
            c for c in self._sub_systems if type(c) == sub_system_type
        ]
        for c in children_to_remove:
            self._sub_systems.remove(c)

    def process(self, *args: Any, **kwargs: Any) -> None:
        """Run all sub-systems"""
        for child in [*self._sub_systems]:
            child.process(*args, **kwargs)


class IComponentFactory(ABC):
    """Abstract base class for factory object that create Component instances"""

    @abstractmethod
    def create(self, world: World, **kwargs: Any) -> Component:
        """
        Create an instance of a component

        Parameters
        ----------
        world: World
            Reference to the World object
        **kwargs: Dict[str, Any]
            Additional keyword parameters

        Returns
        -------
        Component
            Component instance
        """
        raise NotImplementedError


@dataclasses.dataclass()
class ComponentInfo:
    """Information about component classes registered with a World instance

    We use this information to lookup string names mapped to component types,
    and to find the proper factory to use when constructing a component instance
    from a data file or EntityPrefab

    Attributes
    ----------
    name: str
        The name mapped to this component type
    component_type: Type[Component]
        The component class
    factory: IComponentFactory
        A factory instance used to construct the given component type
    """

    name: str
    component_type: Type[Component]
    factory: IComponentFactory


class DefaultComponentFactory(IComponentFactory):
    """
    Constructs instances of a component only using keyword parameters

    Attributes
    ----------
    component_type: Type[Component]
        The type of component that this factory will create
    """

    __slots__ = "component_type"

    def __init__(self, component_type: Type[Component]) -> None:
        super().__init__()
        self.component_type: Type[Component] = component_type

    def create(self, world: World, **kwargs: Any) -> Component:
        """Create a new instance of the component_type using keyword arguments"""
        return self.component_type(**kwargs)


class RootSystemGroup(SystemGroup):
    """This is the top-level system that runs all other systems"""

    group_name = "root"


_T1 = TypeVar("_T1", bound=Component)
_T2 = TypeVar("_T2", bound=Component)
_T3 = TypeVar("_T3", bound=Component)
_T4 = TypeVar("_T4", bound=Component)
_T5 = TypeVar("_T5", bound=Component)
_T6 = TypeVar("_T6", bound=Component)
_T7 = TypeVar("_T7", bound=Component)
_T8 = TypeVar("_T8", bound=Component)


class World:
    """
    Manages Gameobjects, Systems, and resources for the simulation

    Attributes
    ----------
    _ecs: esper.World
        Esper ECS instance used for efficiency
    _gameobjects: Dict[int, GameObject]
        Mapping of GameObjects to unique identifiers
    _dead_gameobjects: List[int]
        List of identifiers for GameObject to remove after
        the latest time step
    _resources: Dict[Type, Any]
        Global resources shared by systems in the ECS
    """

    __slots__ = (
        "_ecs",
        "_gameobjects",
        "_dead_gameobjects",
        "_resources",
        "_component_types",
        "_component_factories",
        "_removed_components",
        "_added_components",
        "_systems",
    )

    def __init__(self) -> None:
        self._ecs: esper.World = esper.World()
        self._gameobjects: Dict[int, GameObject] = {}
        self._dead_gameobjects: OrderedSet[int] = OrderedSet([])
        self._resources: Dict[Type[Any], Any] = {}
        self._component_types: Dict[str, ComponentInfo] = {}
        self._component_factories: Dict[Type[Component], IComponentFactory] = {}
        self._removed_components: DefaultDict[
            Type[Component], OrderedSet[RemovedComponentPair[Any]]
        ] = defaultdict(lambda: OrderedSet([]))
        self._added_components: DefaultDict[
            Type[Component], OrderedSet[int]
        ] = defaultdict(lambda: OrderedSet([]))
        self._systems: SystemGroup = RootSystemGroup()
        # The RootSystemGroup should be the only system that is directly added
        # to esper
        self._ecs.add_processor(self._systems)

    def spawn_gameobject(
        self, components: Optional[List[Component]] = None, name: Optional[str] = None
    ) -> GameObject:
        """Create a new gameobject and attach any given component instances"""
        components_to_add = components if components else []

        entity_id = self._ecs.create_entity()

        gameobject = GameObject(
            unique_id=entity_id,
            world=self,
            name=(name if name else f"GameObject({entity_id})"),
        )

        self._gameobjects[gameobject.uid] = gameobject

        # Add components
        for c in components_to_add:
            gameobject.add_component(c)

        return gameobject

    def get_gameobject(self, gid: int) -> GameObject:
        """Retrieve the GameObject with the given id"""
        try:
            return self._gameobjects[gid]
        except KeyError:
            raise GameObjectNotFoundError(gid)

    def get_gameobjects(self) -> List[GameObject]:
        """Get all gameobjects"""
        return list(self._gameobjects.values())

    def has_gameobject(self, gid: int) -> bool:
        """Check that a GameObject with the given id exists"""
        return gid in self._gameobjects

    def delete_gameobject(self, gid: int) -> None:
        """Remove gameobject from world"""
        gameobject = self._gameobjects[gid]

        gameobject.set_active(False)

        self._dead_gameobjects.append(gid)

        # Recursively remove all children
        for child in gameobject.children:
            self.delete_gameobject(child.uid)

    def add_component(self, gid: int, component: Component) -> None:
        """Add a component to an entity"""
        component.set_gameobject(self._gameobjects[gid])
        component_type = type(component)
        self._added_components[component_type].append(int(gid))
        self._ecs.add_component(int(gid), component)

    def remove_component(self, gid: int, component_type: Type[Component]) -> None:
        """Remove a component from an entity"""

        try:
            if not self.has_component(gid, component_type):
                return

            component = self.get_component_for_entity(gid, component_type)

            self._removed_components[component_type].append(
                RemovedComponentPair(gid, component)
            )

            self._ecs.remove_component(int(gid), component_type)

        except KeyError:
            # This will throw a key error if the GameObject does not
            # have any components.
            return

    def get_component(self, component_type: Type[_CT]) -> List[Tuple[int, _CT]]:
        """Get all the gameobjects that have a given component type"""
        return self._ecs.get_component(component_type)  # type: ignore

    def get_component_for_entity(self, guid: int, component_type: Type[_CT]) -> _CT:
        """Return the component type attached to an entity

        Parameters
        ----------
        guid: int
            The entity to check on
        component_type: Type[_CT]
            The component type to retrieve

        Returns
        -------
        _CT
            The instance of the given component type
        """
        try:
            return self._ecs.component_for_entity(guid, component_type)
        except KeyError:
            raise ComponentNotFoundError(component_type)

    def try_component_for_entity(
        self, guid: int, component_type: Type[_CT]
    ) -> Optional[_CT]:
        """Attempt to return the component type attached to an entity

        Parameters
        ----------
        guid: int
            The entity to check on
        component_type: Type[_CT]
            The component type to retrieve

        Returns
        -------
        _CT or None
            The instance of the given component type
        """
        try:
            return self._ecs.try_component(guid, component_type)
        except KeyError:
            return None

    @overload
    def get_components(
        self, component_types: Tuple[Type[_T1]]
    ) -> List[Tuple[int, Tuple[_T1]]]:
        ...

    @overload
    def get_components(
        self, component_types: Tuple[Type[_T1], Type[_T2]]
    ) -> List[Tuple[int, Tuple[_T1, _T2]]]:
        ...

    @overload
    def get_components(
        self, component_types: Tuple[Type[_T1], Type[_T2], Type[_T3]]
    ) -> List[Tuple[int, Tuple[_T1, _T2, _T3]]]:
        ...

    @overload
    def get_components(
        self, component_types: Tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4]]
    ) -> List[Tuple[int, Tuple[_T1, _T2, _T3, _T4]]]:
        ...

    @overload
    def get_components(
        self,
        component_types: Tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5]],
    ) -> List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5]]]:
        ...

    @overload
    def get_components(
        self,
        component_types: Tuple[
            Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6]
        ],
    ) -> List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6]]]:
        ...

    @overload
    def get_components(
        self,
        component_types: Tuple[
            Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6], Type[_T7]
        ],
    ) -> List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]]:
        ...

    @overload
    def get_components(
        self,
        component_types: Tuple[
            Type[_T1],
            Type[_T2],
            Type[_T3],
            Type[_T4],
            Type[_T5],
            Type[_T6],
            Type[_T7],
            Type[_T8],
        ],
    ) -> List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]]:
        ...

    def get_components(
        self,
        component_types: Union[
            Tuple[Type[_T1]],
            Tuple[Type[_T1], Type[_T2]],
            Tuple[Type[_T1], Type[_T2], Type[_T3]],
            Tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4]],
            Tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5]],
            Tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6]],
            Tuple[
                Type[_T1],
                Type[_T2],
                Type[_T3],
                Type[_T4],
                Type[_T5],
                Type[_T6],
                Type[_T7],
            ],
            Tuple[
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
        List[Tuple[int, Tuple[_T1]]],
        List[Tuple[int, Tuple[_T1, _T2]]],
        List[Tuple[int, Tuple[_T1, _T2, _T3]]],
        List[Tuple[int, Tuple[_T1, _T2, _T3, _T4]]],
        List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5]]],
        List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6]]],
        List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]],
        List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]],
    ]:
        """Get all game objects with the given components"""
        ret = [
            (guid, tuple(components))
            for guid, components in self._ecs.get_components(*component_types)
        ]

        # We have to ignore the type because of esper's lax type hinting for
        # world.get_components()
        return ret  # type: ignore

    def has_components(self, guid: int, *component_types: Type[_CT]) -> bool:
        try:
            return self._ecs.has_components(guid, *component_types)
        except KeyError:
            return False

    def has_component(self, guid: int, component_type: Type[_CT]) -> bool:
        try:
            return self._ecs.has_component(guid, component_type)
        except KeyError:
            return False

    def get_components_for_entity(self, guid: int) -> Tuple[Component, ...]:
        """Get the instances of the component types on the given entity

        Parameters
        ----------
        guid: int
            The entity to check on

        Returns
        -------
        Tuple[Component, ...]
            Component instances
        """
        return self._ecs.components_for_entity(guid)

    def _clear_dead_gameobjects(self) -> None:
        """Delete gameobjects that were removed from the world"""
        for gameobject_id in self._dead_gameobjects:
            if len(self._gameobjects[gameobject_id].get_components()) > 0:
                self._ecs.delete_entity(gameobject_id, True)

            gameobject = self._gameobjects[gameobject_id]

            if gameobject.parent is not None:
                gameobject.parent.remove_child(gameobject)

            del self._gameobjects[gameobject_id]
        self._dead_gameobjects.clear()

    def add_system(self, system: ISystem, priority: Optional[int] = None) -> None:
        """Add a System instance to the World"""
        system.world = self

        if priority is not None:
            system.priority = priority

        stack: List[SystemGroup] = [self._systems]

        while stack:
            current_sys = stack.pop()

            if current_sys.get_name() == system.sys_group:
                current_sys.add_child(system)
                return

            else:
                for c in current_sys.iter_children():
                    if isinstance(c, SystemGroup):
                        stack.append(c)

        raise Exception(f"Could not find system group, {system.sys_group}")

    def get_system(self, system_type: Type[_ST]) -> Optional[_ST]:
        """Get a System of the given type

        Parameters
        ----------
        system_type: Type[_ST]
            The type of the system to retrieve

        Returns
        -------
        Optional[_ST]
            The system instance if one is found
        """
        stack: List[Tuple[SystemGroup, ISystem]] = [
            (self._systems, c) for c in self._systems.iter_children()
        ]

        while stack:
            _, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                return current_sys

            else:
                if isinstance(current_sys, SystemGroup):
                    for c in current_sys.iter_children():
                        stack.append((current_sys, c))

        return None

    def remove_system(self, system_type: Type[ISystem]) -> None:
        """Remove all instances of a system type

        This function performs a Depth-first search through
        the tree of system groups to find the one with the
        matching type.

        No exception is raised if it does not find a matching
        system

        Parameters
        ----------
        system_type: Type[ISystem]
            The type of the system to remove
        """

        stack: List[Tuple[SystemGroup, ISystem]] = [
            (self._systems, c) for c in self._systems.iter_children()
        ]

        while stack:
            group, current_sys = stack.pop()

            if type(current_sys) == system_type:
                group.remove_child(system_type)

            else:
                if isinstance(current_sys, SystemGroup):
                    for c in current_sys.iter_children():
                        stack.append((current_sys, c))

    def step(self, **kwargs: Any) -> None:
        """Call the process method on all systems"""
        self._clear_dead_gameobjects()
        self._ecs.process(**kwargs)  # type: ignore
        self._removed_components.clear()
        self._added_components.clear()

    def add_resource(self, resource: Any) -> None:
        """Add a global resource to the world"""
        resource_type = type(resource)
        if resource_type in self._resources:
            logger.warning(f"Replacing existing resource of type: {resource_type}")
        self._resources[resource_type] = resource

    def remove_resource(self, resource_type: Any) -> None:
        """remove a global resource to the world"""
        try:
            del self._resources[resource_type]
        except KeyError:
            raise ResourceNotFoundError(resource_type)

    def get_resource(self, resource_type: Type[_RT]) -> _RT:
        """Add a global resource to the world"""
        try:
            return self._resources[resource_type]
        except KeyError:
            raise ResourceNotFoundError(resource_type)

    def has_resource(self, resource_type: Any) -> bool:
        """Return true if the world has the given resource"""
        return resource_type in self._resources

    def try_resource(self, resource_type: Type[_RT]) -> Optional[_RT]:
        """Attempt to get resource with type. Return None if not found"""
        return self._resources.get(resource_type)

    def get_all_resources(self) -> List[Any]:
        """Get all resources attached to this World instance"""
        return list(self._resources.values())

    def get_factory(self, component_type: Type[Component]) -> IComponentFactory:
        """Return the factory associate with a component type"""
        return self._component_factories[component_type]

    def get_component_info(self, component_name: str) -> ComponentInfo:
        return self._component_types[component_name]

    def register_component(
        self,
        component_type: Type[Component],
        name: Optional[str] = None,
        factory: Optional[IComponentFactory] = None,
    ) -> None:
        """
        Register component with the engine
        """
        component_name = name if name is not None else component_type.__name__

        self._component_types[component_name] = ComponentInfo(
            name=component_name,
            component_type=component_type,
            factory=(
                factory
                if factory is not None
                else DefaultComponentFactory(component_type)
            ),
        )

        self._component_factories[component_type] = (
            factory if factory is not None else DefaultComponentFactory(component_type)
        )

    def iter_removed_component(
        self, component_type: Type[_CT]
    ) -> Iterator[RemovedComponentPair[_CT]]:
        """Return the IDs of GameObjects that had the given component type added

        Parameters
        ----------
        component_type: Type[Component]
            The component type to check for

        Returns
        -------
        List[int]
            The ID of GameObjects
        """
        return self._removed_components[component_type].__iter__()

    def iter_added_component(self, component_type: Type[Component]) -> Iterator[int]:
        """Return the IDs of GameObjects that had the given component type removed

        Parameters
        ----------
        component_type: Type[Component]
            The component type to check for

        Returns
        -------
        List[int]
            The ID of GameObjects
        """
        return self._added_components[component_type].__iter__()


class EntityPrefab(pydantic.BaseModel):
    """Configuration data for creating a new entity and any children

    Attributes
    ----------
    name: str
        A unique name associated with the prefab
    is_template: bool, optional
        Is this prefab prohibited from being instantiated
        (defaults to False)
    components: Dict[str, Dict[str, Any]]
        Configuration data for components to construct with the prefab mapped
        to the name of the component
    children: List[EntityPrefab]
        Information about child prefabs to instantiate along with this one
    tags: Set[str]
        String tags for filtering
    """

    name: str
    is_template: bool = False
    extends: List[str] = pydantic.Field(default_factory=list)
    components: Dict[str, Dict[str, Any]] = pydantic.Field(default_factory=dict)
    children: List[str] = pydantic.Field(default_factory=list)
    tags: Set[str] = pydantic.Field(default_factory=set)

    @pydantic.validator("extends", pre=True)  # type: ignore
    @classmethod
    def validate_extends(cls, value: Any) -> List[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return value  # type: ignore
        else:
            raise TypeError(f"Expected list str or list of str, but was {type(value)}")


class GameObjectFactory:
    """A static class responsible for managing prefabs and instantiating them"""

    # Stores loaded prefabs in a class variable
    _prefabs: Dict[str, EntityPrefab] = {}

    @classmethod
    def get(cls, prefab_name: str) -> EntityPrefab:
        """Returns an entity prefab"""
        return cls._prefabs[prefab_name]

    @classmethod
    def get_matching_prefabs(cls, *patterns: str) -> List[EntityPrefab]:
        """
        Get all prefabs with names that match the given regex strings

        Parameters
        ----------
        *patterns: Tuple[str, ...]
            Glob-patterns of names to check for

        Returns
        -------
        List[EntityPrefab]
            The names of prefabs in the table that match the pattern
        """

        matches: List[EntityPrefab] = []

        for name, prefab in cls._prefabs.items():
            if any([re.match(p, name) for p in patterns]):
                matches.append(prefab)

        return matches

    @classmethod
    def add(cls, prefab: EntityPrefab) -> None:
        """Add a prefab to the factory"""
        cls._prefabs[prefab.name] = prefab

    @classmethod
    def instantiate(cls, world: World, name: str) -> GameObject:
        """Spawn the prefab into the world and return the root-level entity

        Parameters
        ----------
        world: World
            The World instance to spawn this prefab into
        name: str
            The name of the prefab to instantiate

        Returns
        -------
        GameObject
            A reference to the spawned entity
        """

        # spawn the root gameobject
        prefab = cls._prefabs[name]
        gameobject = world.spawn_gameobject()

        for component_name, component_data in cls._resolve_components(prefab).items():
            try:
                gameobject.add_component(
                    world.get_component_info(component_name).factory.create(
                        world, **component_data
                    )
                )
            except KeyError:
                raise Exception(
                    f"Cannot find component, {component_name}. "
                    "Please ensure that this component has "
                    "been registered with the simulation's world instance."
                )

        for child in prefab.children:
            gameobject.add_child(cls.instantiate(world, child))

        return gameobject

    @classmethod
    def _resolve_components(cls, prefab: EntityPrefab) -> Dict[str, Dict[str, Any]]:
        components: Dict[str, Dict[str, Any]] = {}

        base_components = [
            cls._resolve_components(cls._prefabs[base]) for base in prefab.extends
        ]

        for entry in base_components:
            components.update(entry)

        components.update(prefab.components)

        return components
