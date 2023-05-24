"""Neighborly's Entity Component System

This ECS implementation blends Unity-style GameObjects with the
ECS logic from the Python esper library and the Bevy Game Engine.

This ECS implementation is not thread-safe. It assumes that everything happens
sequentially on the same thread. There some features that were originally designed to
solve multithreading problems in Unity's Entities package. However, they are used here
more for adding reactivity.

Sources:

- https://docs.unity3d.com/ScriptReference/GameObject.html
- https://github.com/benmoran56/esper
- https://github.com/bevyengine/bevy
- https://bevy-cheatbook.github.io/programming/change-detection.html
- https://bevy-cheatbook.github.io/programming/removal-detection.html
- https://docs.unity3d.com/Packages/com.unity.entities@0.1/manual/index.html

"""
from __future__ import annotations

import dataclasses
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

import esper
import pydantic
from ordered_set import OrderedSet

logger = logging.getLogger(__name__)

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")
_ST = TypeVar("_ST", bound="ISystem")
_ET_contra = TypeVar("_ET_contra", bound="Event", contravariant=True)


class ResourceNotFoundError(Exception):
    """Exception raised when attempting to access a resource that does not exist."""

    __slots__ = "resource_type", "message"

    resource_type: Type[Any]
    """The type of the resource."""

    message: str
    """An error message."""

    def __init__(self, resource_type: Type[Any]) -> None:
        """
        Parameters
        ----------
        resource_type
            The type of the resource not found
        """
        super().__init__()
        self.resource_type = resource_type
        self.message = f"Could not find resource with type: {resource_type.__name__}"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(resource_type={})".format(
            self.__class__.__name__, self.resource_type
        )


class GameObjectNotFoundError(Exception):
    """Exception raised when attempting to access a GameObject that does not exist."""

    __slots__ = "gameobject_uid", "message"

    gameobject_uid: int
    """The UID of the desired GameObject."""

    message: str
    """An error message."""

    def __init__(self, gameobject_uid: int) -> None:
        """
        Parameters
        ----------
        gameobject_uid
            The UID of the desired GameObject.
        """
        super().__init__()
        self.gameobject_uid = gameobject_uid
        self.message = f"Could not find GameObject with id: {gameobject_uid}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(gameobject_uid={})".format(
            self.__class__.__name__, self.gameobject_uid
        )


class ComponentNotFoundError(Exception):
    """Exception raised when attempting to retrieve a component that does not exist."""

    __slots__ = "component_type", "message"

    component_type: Type[Component]
    """The type of component not found."""

    message: str
    """An error message."""

    def __init__(self, component_type: Type[Component]) -> None:
        """
        Parameters
        ----------
        component_type
            The desired component type
        """
        super().__init__()
        self.component_type = component_type
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


class ISerializable(ABC):
    """An interface implemented by objects that can be serialized to JSON"""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the object to a Dict.

        Returns
        -------
        Dict[str, Any]
            A dict containing the relevant fields serialized for JSON.
        """
        raise NotImplementedError


class Event(ABC):
    """Events signal when things happen in the simulation"""

    def get_type(self) -> str:
        """Returns the name of the event's type"""
        return self.__class__.__name__


class EventListener(Protocol[_ET_contra]):
    """Callback function that does something in response to an event."""

    def __call__(self, gameobject: GameObject, event: _ET_contra) -> None:
        """
        Do something in response to the event.

        Parameters
        ----------
        gameobject
            The event's target gameobject.
        event
            The event.
        """
        raise NotImplementedError


class GameObject:
    """A reference to an entity within the world.

    GameObjects wrap a unique integer identifier provide an interface to manipulate
    an entity, its components, and its hierarchical relationship with other entities.

    Notes
    -----
    Event listeners are static and shared across all gameobjects.
    """

    _general_event_listeners: ClassVar[List[EventListener[Event]]] = []
    """Event listeners that are called when any event fires."""

    _specific_event_listeners: ClassVar[
        Dict[Type[Event], List[EventListener[Event]]]
    ] = {}
    """Event listeners that are only called when a specific type of event fires."""

    __slots__ = "_id", "name", "_world", "children", "parent"

    _id: int
    """A GameObject's unique ID."""

    _world: World
    """The world instance a GameObject belongs to."""

    name: str
    """The name of the GameObject."""

    children: List[GameObject]
    """Child GameObjects below this one in the hierarchy."""

    parent: Optional[GameObject]
    """The parent GameObject that this GameObject is a child of."""

    def __init__(
        self,
        unique_id: int,
        world: World,
        name: str = "",
    ) -> None:
        """
        Parameters
        ----------
        unique_id
            A unique identifier
        world
            The world instance that this GameObject belongs to
        name
            An optional name to give to the GameObject
            (Defaults to 'GameObject(<unique_id>)')
        """
        self.name = name if name else f"GameObject({unique_id})"
        self._id = unique_id
        self._world = world
        self.parent = None
        self.children = []

    @property
    def uid(self) -> int:
        """A GameObject's ID."""
        return self._id

    @property
    def world(self) -> World:
        """The World instance to which a GameObject belongs."""
        return self._world

    @property
    def exists(self) -> bool:
        """True if a GameObject still exists in the ECS."""
        return self.world.has_gameobject(self._id)

    def get_components(self) -> Tuple[Component, ...]:
        """Get all component instances associated with a GameObject."""
        try:
            return self.world.get_components_for_gameobject(self.uid)
        except KeyError:
            # Ignore errors if gameobject is not found in esper ecs
            return ()

    def get_component_types(self) -> Tuple[Type[Component], ...]:
        """Get the class types of all components attached to a GameObject."""
        return tuple(map(lambda component: type(component), self.get_components()))

    def add_component(self, component: Component) -> None:
        """Add a component to this GameObject.

        Parameters
        ----------
        component
            An instance of a component.

        Notes
        -----
        Adding components is an immediate operation and triggers a ComponentAddedEvent.
        """
        self.world.add_component(self.uid, component)
        self.fire_event(ComponentAddedEvent(component))

    def remove_component(self, component_type: Type[Component]) -> None:
        """Remove a component from the GameObject.

        Parameters
        ----------
        component_type
            The type of the component to remove.

        Notes
        -----
        Removing components is an immediate operation and triggers a
        ComponentRemovedEvent.
        """
        self.fire_event(ComponentRemovedEvent(self.get_component(component_type)))
        self.world.remove_component(self.uid, component_type)

    def get_component(self, component_type: Type[_CT]) -> _CT:
        """Get a component associated with a GameObject.

        Parameters
        ----------
        component_type
            The class type of the component to retrieve.

        Returns
        -------
        _CT
            The instance of the component with the given type.
        """
        return self.world.get_component_for_entity(self.uid, component_type)

    def has_components(self, *component_types: Type[Component]) -> bool:
        """Check if a GameObject has one or more components.

        Parameters
        ----------
        *component_types
            Class types of components to check for.

        Returns
        -------
        bool
            True if all component types are present on a GameObject.
        """
        return self.world.has_components(self.uid, *component_types)

    def has_component(self, component_type: Type[Component]) -> bool:
        """Check if this entity has a component.

        Parameters
        ----------
        component_type
            The class type of the component to check for.

        Returns
        -------
        bool
            True if the component exists, False otherwise.
        """
        return self.world.has_component(self.uid, component_type)

    def try_component(self, component_type: Type[_CT]) -> Optional[_CT]:
        """Try to get a component associated with a GameObject.

        Parameters
        ----------
        component_type
            The class type of the component.

        Returns
        -------
        _CT or None
            The instance of the component.
        """
        try:
            return self.world.try_component_for_entity(self.uid, component_type)
        except KeyError:
            return None

    def add_child(self, gameobject: GameObject) -> None:
        """Add a child GameObject.

        Parameters
        ----------
        gameobject
            A GameObject instance.
        """
        if gameobject.parent is not None:
            gameobject.parent.remove_child(gameobject)
        gameobject.parent = self
        self.children.append(gameobject)

    def remove_child(self, gameobject: GameObject) -> None:
        """Remove a child GameObject.

        Parameters
        ----------
        gameobject
            The GameObject to remove.
        """
        self.children.remove(gameobject)
        gameobject.parent = None

    def get_component_in_child(self, component_type: Type[_CT]) -> Tuple[int, _CT]:
        """Get a single instance of a component type attached to a child.

        Parameters
        ----------
        component_type
            The class type of the component.

        Returns
        -------
        Tuple[int, _CT]
            A tuple containing the ID of the child and an instance of the component.

        Notes
        -----
        Performs a depth-first search of the children and their children and
        returns the first instance of the component type.
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
        """Get all the instances of a component attached to children of a GameObject.

        Parameters
        ----------
        component_type
            The class type of the component

        Returns
        -------
        List[Tuple[int, _CT]]
            A list containing tuples with the ID of the children and the instance of the
            component.
        """
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
        """Remove a GameObject from the world."""
        self.fire_event(GameObjectDestroyedEvent(self))
        self.world.delete_gameobject(self.uid)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the GameObject to a Dict.

        Returns
        -------
        Dict[str, Any]
            A dict containing the relevant fields serialized for JSON.
        """
        ret = {
            "id": self.uid,
            "name": self.name,
            "parent": self.parent.uid if self.parent else -1,
            "children": [c.uid for c in self.children],
            "components": {
                c.__class__.__name__: c.to_dict()
                for c in self.get_components()
                if isinstance(c, ISerializable)
            },
        }

        return ret

    def fire_event(self, event: Event) -> None:
        """Call the registered callbacks to respond to an event.

        Parameters
        ----------
        event
            The fired event.
        """
        for cb in self._general_event_listeners:
            cb(self, event)

        if type(event) in self._specific_event_listeners:
            for cb in self._specific_event_listeners[type(event)]:
                cb(self, event)

    @classmethod
    def on(
        cls,
        event_type: Type[_ET_contra],
        listener: EventListener[_ET_contra],
    ) -> None:
        """Register a listener function to a specific event type.

        Parameters
        ----------
        event_type
            The type of event to listen for.
        listener
            A function to be called when the given event type fires.
        """
        if event_type not in cls._specific_event_listeners:
            cls._specific_event_listeners[event_type] = []
        listener_list = cast(
            List[EventListener[_ET_contra]], cls._specific_event_listeners[event_type]
        )
        listener_list.append(listener)

    @classmethod
    def on_any(cls, listener: EventListener[Event]) -> None:
        """Register a listener function to all event types.

        Parameters
        ----------
        listener
            A function to be called any time an event fires.
        """
        cls._general_event_listeners.append(listener)

    @classmethod
    def clear_event_listeners(cls) -> None:
        """Removes all event listeners from the GameObject class"""
        cls._general_event_listeners.clear()
        cls._specific_event_listeners.clear()

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
            self.__class__.__name__,
            self.uid,
            self.name,
            self.parent,
            [c.uid for c in self.children],
        )


class Component(ABC):
    """A collection of data attributes associated with a GameObject."""

    __slots__ = "_gameobject"

    _gameobject: Optional[GameObject]
    """The GameObject a component belongs to."""

    def __init__(self) -> None:
        super().__init__()
        self._gameobject = None

    @property
    def gameobject(self) -> GameObject:
        """The GameObject a component belongs to."""
        if self._gameobject is None:
            raise TypeError("Component's GameObject is None")
        return self._gameobject

    def set_gameobject(self, gameobject: Optional[GameObject]) -> None:
        """
        Set the gameobject instance for this component.

        Parameters
        ----------
        gameobject
            The GameObject instance or None if being removed from a GameObject.
        """
        self._gameobject = gameobject


class ISystem(ABC, esper.Processor):
    """Abstract base class implementation for ECS systems."""

    sys_group: ClassVar[str] = "root"
    """The system group this system belongs to."""

    # We have to re-type the 'world' class variable because
    # it is declared as 'Any' by esper, and we need it to
    # be of type World
    world: ClassVar[World]  # type: ignore
    """The world instance this system belongs to."""

    active: ClassVar[bool] = True
    """Will this system run during the next simulation step."""

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> None:
        """Perform operations for a single simulation step.

        Parameters
        ----------
        *args
            Positional arguments for the system.
        **kwargs
            Keyword arguments for the system.
        """
        raise NotImplementedError

    @classmethod
    def get_world(cls) -> World:
        """Get the system's world instance.

        Returns
        -------
        World
            The world the system belongs to.
        """
        return cls.world


class SystemGroup(ISystem, ABC):
    """A group of ECS systems that run as a unit.

    Notes
    -----
    Since groups are themselves systems, SystemGroups allow users to better structure
    the execution order of their systems.
    """

    group_name: ClassVar[str] = ""
    """The name associated with this system group."""

    __slots__ = "_sub_systems"

    _sub_systems: List[ISystem]
    """The systems that belong to this group"""

    def __init__(self) -> None:
        super().__init__()
        self._sub_systems = []

    @classmethod
    def get_name(cls) -> str:
        """Get the name of the group.

        Returns
        -------
        str
            The name of the group.
        """
        return cls.group_name

    def iter_children(self) -> Iterator[ISystem]:
        """Get an iterator for the group's children.

        Returns
        -------
        Iterator[ISystem]
            An iterator for the child system collection.
        """
        return self._sub_systems.__iter__()

    def add_child(self, sub_system: ISystem) -> None:
        """Add a new system as a sub_system of this group.

        Parameters
        ----------
        sub_system
            The system to add to this group.
        """
        self._sub_systems.append(sub_system)
        self._sub_systems.sort(key=lambda s: s.priority, reverse=True)

    def remove_child(self, sub_system_type: Type[ISystem]) -> None:
        """Remove a child system.

        Parameters
        ----------
        sub_system_type
            The class type of the system to remove.
        """
        children_to_remove = [
            c for c in self._sub_systems if type(c) == sub_system_type
        ]
        for c in children_to_remove:
            self._sub_systems.remove(c)

    def process(self, *args: Any, **kwargs: Any) -> None:
        """Run all sub-systems.

        Parameters
        ----------
        *args
            Positional arguments to pass to all subsystems.
        **kwargs
            Keyword arguments to pass to all subsystems.
        """
        if type(self).active is False:
            return

        for child in [*self._sub_systems]:
            if type(child).active:
                child.process(*args, **kwargs)


class IComponentFactory(ABC):
    """Abstract base class for factory object that create Component instances"""

    @abstractmethod
    def create(self, world: World, **kwargs: Any) -> Component:
        """
        Create an instance of a component

        Parameters
        ----------
        world
            Reference to the World object
        **kwargs
            Additional keyword parameters

        Returns
        -------
        Component
            Component instance
        """
        raise NotImplementedError


@dataclasses.dataclass()
class ComponentInfo:
    """Information about component classes registered with a World instance.

    Notes
    -----
    We use this information to lookup string names mapped to component types,
    and to find the proper factory to use when constructing a component instance
    from a data file or EntityPrefab.
    """

    name: str
    """The name mapped to this component type."""

    component_type: Type[Component]
    """The component class."""

    factory: IComponentFactory
    """A factory instance used to construct the given component type."""


class DefaultComponentFactory(IComponentFactory):
    """Constructs instances of a component only using keyword parameters."""

    __slots__ = "component_type"

    component_type: Type[Component]
    """The type of component that this factory will create."""

    def __init__(self, component_type: Type[Component]) -> None:
        """
        Parameters
        ----------
        component_type
            The class type of the component this factory will make.
        """
        super().__init__()
        self.component_type = component_type

    def create(self, world: World, **kwargs: Any) -> Component:
        """Create a new instance of the component_type using keyword arguments."""
        return self.component_type(**kwargs)


class RootSystemGroup(SystemGroup):
    """This is the top-level system that runs all other systems."""

    group_name = "root"


@dataclass
class ComponentAddedEvent(Event):
    """An event fired when a component is added to a GameObject."""

    component: Component
    """A reference to the added component."""


@dataclass
class ComponentRemovedEvent(Event):
    """An event fired when a component is removed from a GameObject."""

    component: Component
    """A reference to the removed component."""


@dataclass
class GameObjectDestroyedEvent(Event):
    """An event fired when a GameObject is destroyed."""

    gameobject: GameObject
    """A reference to the GameObject to be destroyed."""


_T1 = TypeVar("_T1", bound=Component)
_T2 = TypeVar("_T2", bound=Component)
_T3 = TypeVar("_T3", bound=Component)
_T4 = TypeVar("_T4", bound=Component)
_T5 = TypeVar("_T5", bound=Component)
_T6 = TypeVar("_T6", bound=Component)
_T7 = TypeVar("_T7", bound=Component)
_T8 = TypeVar("_T8", bound=Component)


class World:
    """Manages Gameobjects, Systems, and resources."""

    __slots__ = (
        "_ecs",
        "_gameobjects",
        "_dead_gameobjects",
        "_resources",
        "_component_types",
        "_component_factories",
        "_systems",
    )

    _ecs: esper.World
    """Esper ECS instance used for efficiency."""

    _gameobjects: Dict[int, GameObject]
    """Mapping of GameObjects to unique identifiers."""

    _dead_gameobjects: OrderedSet[int]
    """IDs of GameObjects to clean-up following destruction."""

    _resources: Dict[Type[Any], Any]
    """Global resources shared by systems in the ECS."""

    _component_types: Dict[str, ComponentInfo]
    """Information about components that have been registered with the ECS."""

    _component_factories: Dict[Type[Component], IComponentFactory]
    """Component types mapped to their registered factories."""

    _systems: SystemGroup
    """The systems run every simulation step."""

    def __init__(self) -> None:
        self._ecs = esper.World()
        self._gameobjects = {}
        self._dead_gameobjects = OrderedSet([])
        self._resources = {}
        self._component_types = {}
        self._component_factories = {}
        self._systems = RootSystemGroup()
        # The RootSystemGroup should be the only system that is directly added
        # to esper
        self._ecs.add_processor(self._systems)

    def spawn_gameobject(
        self, components: Optional[List[Component]] = None, name: Optional[str] = None
    ) -> GameObject:
        """Create a new gameobject and attach any given component instances.

        Parameters
        ----------
        components
            The components to add to the GameObject
        name
            A string name for the GameObject

        Returns
        -------
        GameObject
            The newly instantiated GameObject with any starting components.
        """
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

    def get_gameobject(self, uid: int) -> GameObject:
        """Get a GameObject.

        Parameters
        ----------
        uid
            The ID of the GameObject.

        Returns
        -------
        GameObject
            The GameObject with the given ID.
        """
        try:
            return self._gameobjects[uid]
        except KeyError:
            raise GameObjectNotFoundError(uid)

    def get_gameobjects(self) -> List[GameObject]:
        """Get all gameobjects.

        Returns
        -------
        List[GameObject]
            All the GameObjects that exist in the world.
        """
        return list(self._gameobjects.values())

    def has_gameobject(self, uid: int) -> bool:
        """Check that a GameObject exists.

        Parameters
        ----------
        uid
            The ID of the GameObject to check for.

        Returns
        -------
        bool
            True if the GameObject exists.
        """
        return uid in self._gameobjects

    def delete_gameobject(self, uid: int) -> None:
        """Remove a gameobject from the world.

        Parameters
        ----------
        uid
            The ID of the GameObject to remove.
        """
        gameobject = self._gameobjects[uid]

        self._dead_gameobjects.append(uid)

        # Recursively remove all children
        for child in gameobject.children:
            self.delete_gameobject(child.uid)

    def add_component(self, uid: int, component: Component) -> None:
        """Add a component to a GameObject.

        Parameters
        ----------
        uid
            The ID of the GameObject to add the component to.
        component
            The component instance to add.
        """
        component.set_gameobject(self._gameobjects[uid])
        self._ecs.add_component(uid, component)

    def remove_component(self, uid: int, component_type: Type[Component]) -> None:
        """Remove a component from a GameObject.

        Parameters
        ----------
        uid
            The ID of the GameObject to remove the component from.
        component_type
            The class type of the component to remove.
        """

        try:
            if not self.has_component(uid, component_type):
                return

            self._ecs.remove_component(uid, component_type)

        except KeyError:
            # This will throw a key error if the GameObject does not
            # have any components.
            return

    def get_component(self, component_type: Type[_CT]) -> List[Tuple[int, _CT]]:
        """Get all the GameObjects that have a given component type.

        Parameters
        ----------
        component_type
            The component type to check for.

        Returns
        -------
        List[Tuple[int, _CT]]
            A list of tuples containing the ID of a GameObject and its respective
            component instance.
        """
        return self._ecs.get_component(component_type)  # type: ignore

    def get_component_for_entity(self, uid: int, component_type: Type[_CT]) -> _CT:
        """Return the component type attached to an entity

        Parameters
        ----------
        uid
            The ID of a GameObject to get the component from
        component_type
            The component type to retrieve

        Returns
        -------
        _CT
            The instance of the given component type
        """
        try:
            return self._ecs.component_for_entity(uid, component_type)
        except KeyError:
            raise ComponentNotFoundError(component_type)

    def try_component_for_entity(
        self, uid: int, component_type: Type[_CT]
    ) -> Optional[_CT]:
        """Attempt to get a component attached to a GameObject

        Parameters
        ----------
        uid
            The entity to check on
        component_type
            The component type to retrieve

        Returns
        -------
        _CT or None
            The instance of the given component type
        """
        try:
            return self._ecs.try_component(uid, component_type)
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
        """Get all game objects with the given components.

        Parameters
        ----------
        component_types
            The components to check for

        Returns
        -------
        Union[
            List[Tuple[int, Tuple[_T1]]],
            List[Tuple[int, Tuple[_T1, _T2]]],
            List[Tuple[int, Tuple[_T1, _T2, _T3]]],
            List[Tuple[int, Tuple[_T1, _T2, _T3, _T4]]],
            List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5]]],
            List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6]]],
            List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]],
            List[Tuple[int, Tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]],
        ]
            List of tuples containing a GameObject ID and an additional tuple with
            the instances of the given component types, in-order.
        """
        ret = [
            (uid, tuple(components))
            for uid, components in self._ecs.get_components(*component_types)
        ]

        # We have to ignore the type because of esper's lax type hinting for
        # world.get_components()
        return ret  # type: ignore

    def has_components(self, uid: int, *component_types: Type[_CT]) -> bool:
        """Check if a GameObject has one or more components.

        Parameters
        ----------
        uid
            The ID of the GameObject to check.
        *component_types
            The component types to check for.

        Returns
        -------
        bool
            True if the components are present of the GameObject, false otherwise.
        """
        try:
            return self._ecs.has_components(uid, *component_types)
        except KeyError:
            return False

    def has_component(self, uid: int, component_type: Type[_CT]) -> bool:
        """Check if a GameObject has a component.

        Parameters
        ----------
        uid
            The ID of the GameObject to check.
        component_type
            The component types to check for.

        Returns
        -------
        bool
            True if the component is present of the GameObject, false otherwise.
        """
        try:
            return self._ecs.has_component(uid, component_type)
        except KeyError:
            return False

    def get_components_for_gameobject(self, uid: int) -> Tuple[Component, ...]:
        """Get all components associated with a GameObject.

        Parameters
        ----------
        uid
            The ID of a GameObject.

        Returns
        -------
        Tuple[Component, ...]
            A tuple containing all the component instances attached to this GameObject.
        """
        return self._ecs.components_for_entity(uid)

    def _clear_dead_gameobjects(self) -> None:
        """Delete gameobjects that were removed from the world."""
        for gameobject_id in self._dead_gameobjects:
            if len(self._gameobjects[gameobject_id].get_components()) > 0:
                self._ecs.delete_entity(gameobject_id, True)

            gameobject = self._gameobjects[gameobject_id]

            if gameobject.parent is not None:
                gameobject.parent.remove_child(gameobject)

            del self._gameobjects[gameobject_id]
        self._dead_gameobjects.clear()

    def add_system(self, system: ISystem, priority: Optional[int] = None) -> None:
        """Add a System instance.

        Parameters
        ----------
        system
            The system to add.
        priority
            The priority of the system relative to the others in it's system group.
        """
        type(system).world = self

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
        """Attempt to get a System of the given type.

        Parameters
        ----------
        system_type
            The type of the system to retrieve.

        Returns
        -------
        _ST or None
            The system instance if one is found.
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
        """Remove all instances of a system type.

        Parameters
        ----------
        system_type
            The type of the system to remove.

        Notes
        -----
        This function performs a Depth-first search through
        the tree of system groups to find the one with the
        matching type.

        No exception is raised if it does not find a matching
        system.
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
        """Advance the simulation as single tick and call all the systems.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the systems.
        """
        self._clear_dead_gameobjects()
        self._ecs.process(**kwargs)  # type: ignore

    def add_resource(self, resource: Any) -> None:
        """Add a shared resource to a world.

        Parameters
        ----------
        resource
            The resource to add
        """
        resource_type = type(resource)
        if resource_type in self._resources:
            logger.warning(f"Replacing existing resource of type: {resource_type}")
        self._resources[resource_type] = resource

    def remove_resource(self, resource_type: Any) -> None:
        """Remove a shared resource to a world.

        Parameters
        ----------
        resource_type
            The class type of the resource.
        """
        try:
            del self._resources[resource_type]
        except KeyError:
            raise ResourceNotFoundError(resource_type)

    def get_resource(self, resource_type: Type[_RT]) -> _RT:
        """Access a shared resource.

        Parameters
        ----------
        resource_type
            The class type of a resource.

        Returns
        -------
        _RT
            The instance of the resource.
        """
        try:
            return self._resources[resource_type]
        except KeyError:
            raise ResourceNotFoundError(resource_type)

    def has_resource(self, resource_type: Type[Any]) -> bool:
        """Check if a world has a shared resource.

        Parameters
        ----------
        resource_type
            The class type of a resource.

        Returns
        -------
        bool
            True if the resource exists, False otherwise.
        """
        return resource_type in self._resources

    def try_resource(self, resource_type: Type[_RT]) -> Optional[_RT]:
        """Attempt to access a shared resource.

        Parameters
        ----------
        resource_type
            The class type of a resource.

        Returns
        -------
        _RT or None
            The instance of the resource.
        """
        return self._resources.get(resource_type)

    def get_all_resources(self) -> List[Any]:
        """Get all resources attached to a World instance.

        Returns
        -------
        List[Any]
            A list of all the attached resources.
        """
        return list(self._resources.values())

    def get_factory(self, component_type: Type[Component]) -> IComponentFactory:
        """Return the factory associated with a component type.

        Parameters
        ----------
        component_type
            The class type of a component.

        Returns
        -------
        IComponentFactory
            The component factory associated with the given component type.
        """
        return self._component_factories[component_type]

    def get_component_info(self, component_name: str) -> ComponentInfo:
        """Get information about a component class type.

        Parameters
        ----------
        component_name
            The string name of the component.

        Returns
        -------
        ComponentInfo
            Information about the desired component class type.
        """
        return self._component_types[component_name]

    def register_component(
        self,
        component_type: Type[Component],
        name: Optional[str] = None,
        factory: Optional[IComponentFactory] = None,
    ) -> None:
        """Register a component class type with the engine.

        Parameters
        ----------
        component_type
            The class type of a component.
        name
            An alternative name used to reference the component in EntityPrefabs.
        factory
            A factory used to construct this component type.
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


class EntityPrefab(pydantic.BaseModel):
    """Configuration data for creating a new entity and any children."""

    name: str
    """A unique name associated with the prefab."""

    is_template: bool = False
    """Is this prefab prohibited from being instantiated (defaults to False)."""

    extends: List[str] = pydantic.Field(default_factory=list)
    """Names of prefabs that this prefab inherits component definitions from."""

    components: Dict[str, Dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Configuration data for components to construct on the prefab."""

    children: List[str] = pydantic.Field(default_factory=list)
    """Information about child prefabs to instantiate along with this one."""

    tags: Set[str] = pydantic.Field(default_factory=set)
    """String tags for filtering."""

    @pydantic.validator("extends", pre=True)  # type: ignore
    @classmethod
    def _validate_extends(cls, value: Any) -> List[str]:
        """Ensures the `extends` field is a list of str."""
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return value  # type: ignore
        else:
            raise TypeError(f"Expected list str or list of str, but was {type(value)}")


class GameObjectFactory:
    """A static class responsible for managing and instantiating prefabs."""

    _prefabs: ClassVar[Dict[str, EntityPrefab]] = {}
    """Stores loaded prefabs"""

    @classmethod
    def get(cls, prefab_name: str) -> EntityPrefab:
        """Retrieve an entity prefab

        Parameters
        ----------
        prefab_name
            The name of the prefab
        """
        return cls._prefabs[prefab_name]

    @classmethod
    def get_matching_prefabs(cls, *patterns: str) -> List[EntityPrefab]:
        """
        Get all prefabs with names that match the given regex strings.

        Parameters
        ----------
        *patterns
            Glob-patterns of names to check for.

        Returns
        -------
        List[EntityPrefab]
            The names of prefabs in the table that match the pattern.
        """

        matches: List[EntityPrefab] = []

        for name, prefab in cls._prefabs.items():
            if any([re.match(p, name) for p in patterns]):
                matches.append(prefab)

        return matches

    @classmethod
    def add(cls, prefab: EntityPrefab) -> None:
        """Add a prefab to the factory.

        Parameters
        ----------
        prefab
            The prefab to add.
        """
        cls._prefabs[prefab.name] = prefab

    @classmethod
    def instantiate(cls, world: World, name: str) -> GameObject:
        """Spawn the prefab into the world and return the root-level entity.

        Parameters
        ----------
        world
            The World instance to spawn this prefab into.
        name
            The name of the prefab to instantiate.

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
        """Create the aggregate collection of components for a prefab and its templates.

        Thi function traverses the inheritance tree of prefabs and creates the final
        collection of components that will be constructed for an instance of the given
        prefab.

        Parameters
        ----------
        prefab
            The prefab to use.

        Returns
        -------
        Dict[str, Dict[str, Any]]
            The map of component names mapped to keyword arguments to pass to their
            factories.
        """
        components: Dict[str, Dict[str, Any]] = {}

        base_components = [
            cls._resolve_components(cls._prefabs[base]) for base in prefab.extends
        ]

        for entry in base_components:
            components.update(entry)

        components.update(prefab.components)

        return components


class Active(Component, ISerializable):
    """Tags a GameObject as active within the simulation."""

    def to_dict(self) -> Dict[str, Any]:
        return {}
