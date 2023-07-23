"""Neighborly's Entity Component System

This ECS implementation blends Unity-style GameObjects with the
ECS logic from the Python esper library and the Bevy Game Engine.

This ECS implementation is not thread-safe. It assumes that everything happens
sequentially on the same thread.

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
import json
import logging
import re
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Iterable,
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
from pydantic import ValidationError

_LOGGER = logging.getLogger(__name__)

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")
_ST = TypeVar("_ST", bound="ISystem")
_ET_contra = TypeVar("_ET_contra", bound="Event", contravariant=True)


class ResourceNotFoundError(Exception):
    """Exception raised when attempting to access a resource that does not exist."""

    __slots__ = "resource_type", "message"

    resource_type: Type[Any]
    """The class type of the resource."""

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
        self.message = f"Could not find resource with type: {resource_type.__name__}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(resource_type={})".format(
            self.__class__.__name__, self.resource_type
        )


class SystemNotFoundError(Exception):
    """Exception raised when attempting to access a system that does not exist."""

    __slots__ = "system_type", "message"

    system_type: Type[Any]
    """The class type of the system."""

    message: str
    """An error message."""

    def __init__(self, system_type: Type[Any]) -> None:
        """
        Parameters
        ----------
        system_type
            The type of the resource not found
        """
        super().__init__()
        self.system_type = system_type
        self.message = f"Could not find system with type: {system_type.__name__}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(resource_type={})".format(self.__class__.__name__, self.system_type)


class GameObjectNotFoundError(Exception):
    """Exception raised when attempting to access a GameObject that does not exist."""

    __slots__ = "gameobject_id", "message"

    gameobject_id: int
    """The ID of the desired GameObject."""

    message: str
    """An error message."""

    def __init__(self, gameobject_id: int) -> None:
        """
        Parameters
        ----------
        gameobject_id
            The UID of the desired GameObject.
        """
        super().__init__()
        self.gameobject_id = gameobject_id
        self.message = f"Could not find GameObject with id: {gameobject_id}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(gameobject_uid={})".format(
            self.__class__.__name__, self.gameobject_id
        )


class ComponentNotFoundError(Exception):
    """Exception raised when attempting to access a component that does not exist."""

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
        self.message = "Could not find Component with type: '{}'.".format(
            component_type.__name__
        )

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(component_type={})".format(
            self.__class__.__name__,
            self.component_type.__name__,
        )


class MissingPrefabError(Exception):
    """Exception raised when attempting to access a prefab that does not exist."""

    __slots__ = "prefab_name", "message"

    prefab_name: str
    """The type of component not found."""

    message: str
    """An error message."""

    def __init__(self, prefab_name: str) -> None:
        """
        Parameters
        ----------
        prefab_name
            The name of a prefab definition
        """
        super().__init__()
        self.prefab_name = prefab_name
        self.message = "Could not find GameObjectPrefab with name: '{}'.".format(
            prefab_name
        )

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(prefab_name={})".format(
            self.__class__.__name__,
            self.prefab_name,
        )


class ISerializable(ABC):
    """An interface implemented by objects that can be serialized to JSON."""

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
    """Events signal when things happen in the simulation."""

    __slots__ = "_world"

    _world: World
    """The world instance to fire this event on."""

    def __init__(self, world: World) -> None:
        self._world = world

    @property
    def world(self) -> World:
        return self._world

    def get_type(self) -> str:
        """Returns the name of the event's type"""
        return self.__class__.__name__

    def dispatch(self) -> None:
        """Dispatch the event to registered event listeners."""
        self.world.event_manager.dispatch_event(self)


class EventListener(Protocol[_ET_contra]):
    """Callback function that does something in response to an event."""

    def __call__(self, event: _ET_contra) -> None:
        """Do something in response to the event.

        Parameters
        ----------
        event
            The event.
        """
        raise NotImplementedError


class GameObject:
    """A reference to an entity within the world.

    GameObjects wrap a unique integer identifier and provide an interface to access
    associated components and child/parent gameobjects.
    """

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
        """Check if the GameObject still exists in the ECS.

        Returns
        -------
        bool
            True if the GameObject exists, False otherwise.
        """
        return self.world.gameobject_manager.has_gameobject(self)

    def activate(self) -> None:
        """Tag the GameObject as active."""
        self.add_component(Active())

    def deactivate(self) -> None:
        """Remove the Active tag from a GameObject."""
        self.remove_component(Active)

    def get_components(self) -> Tuple[Component, ...]:
        """Get all components associated with the GameObject.

        Returns
        -------
        Tuple[Component, ...]
            Component instances
        """
        try:
            return self.world.gameobject_manager.get_components_for_gameobject(self)
        except KeyError:
            # Ignore errors if gameobject is not found in esper ecs
            return ()

    def get_component_types(self) -> Tuple[Type[Component], ...]:
        """Get the class types of all components attached to the GameObject.

        Returns
        -------
        Tuple[Type[Component], ...]
            Collection of component types.
        """
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
        self.world.gameobject_manager.add_component(self, component)

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
        self.world.gameobject_manager.remove_component(self, component_type)

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
        return self.world.gameobject_manager.get_component_for_gameobject(
            self, component_type
        )

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
        return self.world.gameobject_manager.has_components(self, *component_types)

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
        return self.world.gameobject_manager.has_component(self, component_type)

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
            return self.world.gameobject_manager.try_component_for_gameobject(
                self, component_type
            )
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
        self.world.gameobject_manager.destroy_gameobject(self)

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
                c.__class__.__name__: json.loads(json.dumps(c.to_dict()))
                for c in self.get_components()
                if isinstance(c, ISerializable)
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
            self.__class__.__name__,
            self.uid,
            self.name,
            self.parent,
            [c.uid for c in self.children],
        )


class Component(ABC):
    """A collection of data attributes associated with a GameObject."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()

    def on_add(self, gameobject: GameObject) -> None:
        """Lifecycle method called when a component is added to a GameObject.

        Parameters
        ----------
        gameobject
            The GameObject the status is attached to.
        """
        return

    def on_remove(self, gameobject: GameObject) -> None:
        """Lifecycle method called when a component is removed from a GameObject.

        Parameters
        ----------
        gameobject
            The GameObject the status going to be removed from.
        """
        return

    @classmethod
    def on_register(cls, world: World) -> None:
        """Lifecycle method called when a component class is registered."""
        pass


class TagComponent(Component, ISerializable):
    """An Empty component used to mark a GameObject as having a state or type."""

    def to_dict(self) -> Dict[str, Any]:
        return {}

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class Active(TagComponent):
    """Tags a GameObject as active within the simulation."""

    pass


class ISystem(ABC):
    """Abstract Interface for ECS systems."""

    @abstractmethod
    def set_active(self, value: bool) -> None:
        """Toggle if this system is active and will update.

        Parameters
        ----------
        value
            The new active status.
        """
        raise NotImplementedError

    @abstractmethod
    def on_create(self, world: World) -> None:
        """Lifecycle method called when the system is added to the world.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        raise NotImplementedError

    @abstractmethod
    def on_start_running(self, world: World) -> None:
        """Lifecycle method called before checking if a system will update.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        raise NotImplementedError

    @abstractmethod
    def on_destroy(self, world: World) -> None:
        """Lifecycle method called when a system is removed from the world.

        Parameters
        ----------
        world
            The world instance the system was removed from.
        """
        raise NotImplementedError

    @abstractmethod
    def on_update(self, world: World) -> None:
        """Lifecycle method called each when stepping the simulation.

        Parameters
        ----------
        world
            The world instance the system is updating
        """
        raise NotImplementedError

    @abstractmethod
    def on_stop_running(self, world: World) -> None:
        """Lifecycle method called after a system will updates.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        raise NotImplementedError

    @abstractmethod
    def should_run_system(self, world: World) -> bool:
        """Checks if this system should run this simulation step."""
        raise NotImplementedError


class SystemBase(ISystem, ABC):
    """Abstract base class for ECS systems that provides default implementation for most lifecycle methods."""

    _active: bool
    """Will this system update during the next simulation step."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self._active = True

    def set_active(self, value: bool) -> None:
        """Toggle if this system is active and will update.

        Parameters
        ----------
        value
            The new active status.
        """
        self._active = value

    def on_create(self, world: World) -> None:
        """Lifecycle method called when the system is added to the world.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        return

    def on_start_running(self, world: World) -> None:
        """Lifecycle method called before checking if a system will update.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        return

    def on_destroy(self, world: World) -> None:
        """Lifecycle method called when a system is removed from the world.

        Parameters
        ----------
        world
            The world instance the system was removed from.
        """
        return

    def on_stop_running(self, world: World) -> None:
        """Lifecycle method called after a system will updates.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        return

    def should_run_system(self, world: World) -> bool:
        """Checks if this system should run this simulation step."""
        return self._active


class SystemGroup(SystemBase, ABC):
    """A group of ECS systems that run as a unit.

    SystemGroups allow users to better structure the execution order of their systems.
    """

    __slots__ = "_children"

    _children: List[Tuple[int, SystemBase]]
    """The systems that belong to this group"""

    def __init__(self) -> None:
        super().__init__()
        self._children = []

    def iter_children(self) -> Iterator[Tuple[int, SystemBase]]:
        """Get an iterator for the group's children.

        Returns
        -------
        Iterator[Tuple[SystemBase]]
            An iterator for the child system collection.
        """
        return self._children.__iter__()

    def add_child(self, system: SystemBase, priority: int = 0) -> None:
        """Add a new system as a sub_system of this group.

        Parameters
        ----------
        system
            The system to add to this group.
        priority
            The priority of running this system relative to its siblings.
        """
        self._children.append((priority, system))
        self._children.sort(key=lambda pair: pair[0], reverse=True)

    def remove_child(self, system_type: Type[SystemBase]) -> None:
        """Remove a child system.

        If for some reason there are more than one instance of the given system type,
        this method will remove the first instance it finds.

        Parameters
        ----------
        system_type
            The class type of the system to remove.
        """
        children_to_remove = [
            pair for pair in self._children if type(pair[1]) == system_type
        ]

        if children_to_remove:
            self._children.remove(children_to_remove[0])

    def on_update(self, world: World) -> None:
        """Run all sub-systems.

        Parameters
        ----------
        world
            The world instance the system is updating
        """
        for _, child in self._children:
            child.on_start_running(world)
            if child.should_run_system(world):
                child.on_update(world)
            child.on_stop_running(world)


class SystemManager(SystemGroup):
    """Manages system instances for a single world instance."""

    __slots__ = "world"

    _world: World
    """The world instance associated with the SystemManager."""

    def __init__(self, world: World) -> None:
        super().__init__()
        self.world = world

    def add_system(
        self,
        system: SystemBase,
        priority: int = 0,
        system_group: Optional[Type[SystemGroup]] = None,
    ) -> None:
        """Add a System instance.

        Parameters
        ----------
        system
            The system to add.
        priority
            The priority of the system relative to the others in its system group.
        system_group
            The class of the group to add this system to
        """

        if system_group is None:
            self.add_child(system, priority)
            return

        stack = [child for _, child in self._children]

        while stack:
            current_sys = stack.pop()

            if isinstance(current_sys, system_group):
                current_sys.add_child(system)
                system.on_create(self.world)
                return

            elif isinstance(current_sys, SystemGroup):
                for _, child in current_sys.iter_children():
                    stack.append(child)

        raise SystemNotFoundError(system_group)

    def get_system(self, system_type: Type[_ST]) -> _ST:
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
        stack: List[Tuple[SystemGroup, SystemBase]] = [
            (self, child) for _, child in self._children
        ]

        while stack:
            _, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                return current_sys

            else:
                if isinstance(current_sys, SystemGroup):
                    for _, child in current_sys.iter_children():
                        stack.append((current_sys, child))

        raise SystemNotFoundError(system_type)

    def remove_system(self, system_type: Type[SystemBase]) -> None:
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

        stack: List[Tuple[SystemGroup, SystemBase]] = [
            (self, c) for _, c in self.iter_children()
        ]

        while stack:
            group, current_sys = stack.pop()

            if type(current_sys) == system_type:
                group.remove_child(system_type)
                current_sys.on_destroy(self.world)

            else:
                if isinstance(current_sys, SystemGroup):
                    for _, child in current_sys.iter_children():
                        stack.append((current_sys, child))

    def update_systems(self) -> None:
        """Update all systems in the manager."""
        self.on_update(self.world)


class IComponentFactory(ABC):
    """Abstract base class for factory object that create Component instances"""

    def __init__(self, **kwargs: Any) -> None:
        pass

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


class ResourceManager:
    """Manages shared resources for a world instance."""

    __slots__ = "_resources", "_world"

    _world: World
    """The world instance associated with the SystemManager."""

    _resources: Dict[Type[Any], Any]
    """Resources shared by the world instance."""

    def __init__(self, world: World) -> None:
        self._world = world
        self._resources = {}

    def add_resource(self, resource: Any) -> None:
        """Add a shared resource to a world.

        Parameters
        ----------
        resource
            The resource to add
        """
        resource_type = type(resource)
        if resource_type in self._resources:
            _LOGGER.warning(f"Replacing existing resource of type: {resource_type}")
        self._resources[resource_type] = resource

    def remove_resource(self, resource_type: Type[Any]) -> None:
        """Remove a shared resource to a world.

        Parameters
        ----------
        resource_type
            The class of the resource.
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
            The class of the resource.

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
            The class of the resource.

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
            The class of the resource.

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


class EventManager:
    """Manages event listeners for a single World instance."""

    __slots__ = "_general_event_listeners", "_event_listeners_by_type", "_world"

    _world: World
    """The world instance associated with the SystemManager."""

    _general_event_listeners: OrderedSet[EventListener[Event]]
    """Event listeners that are called when any event fires."""

    _event_listeners_by_type: Dict[Type[Event], OrderedSet[EventListener[Event]]]
    """Event listeners that are only called when a specific type of event fires."""

    def __init__(self, world: World) -> None:
        self._world = world
        self._general_event_listeners = OrderedSet([])
        self._event_listeners_by_type = {}

    def on_event(
        self,
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
        if event_type not in self._event_listeners_by_type:
            self._event_listeners_by_type[event_type] = OrderedSet([])
        listener_set = cast(
            OrderedSet[EventListener[_ET_contra]],
            self._event_listeners_by_type[event_type],
        )
        listener_set.add(listener)

    def on_any_event(self, listener: EventListener[Event]) -> None:
        """Register a listener function to all event types.

        Parameters
        ----------
        listener
            A function to be called any time an event fires.
        """
        self._general_event_listeners.append(listener)

    def dispatch_event(self, event: Event) -> None:
        """Fire an event and trigger associated event listeners.

        Parameters
        ----------
        event
            The event to fire
        """
        for callback_fn in self._event_listeners_by_type.get(
            type(event), OrderedSet([])
        ):
            callback_fn(event)

        for callback_fn in self._general_event_listeners:
            callback_fn(event)


class GameObjectPrefab(pydantic.BaseModel):
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

    metadata: Dict[str, Any] = pydantic.Field(default_factory=dict)
    """Additional information about this prefab."""

    # noinspection PyNestedDecorators
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

    # noinspection PyNestedDecorators
    @pydantic.validator("extends", pre=True)  # type: ignore
    @classmethod
    def _validate_tags(cls, value: Any) -> Set[str]:
        """Ensures the `extends` field is a list of str."""
        if isinstance(value, str):
            return {value}
        if isinstance(value, list):
            return set(value)  # type: ignore
        if isinstance(value, set):
            return value  # type: ignore
        else:
            raise TypeError(f"Expected list str or list of str, but was {type(value)}")

    @classmethod
    def from_raw(cls, data: Dict[str, Any]) -> GameObjectPrefab:
        try:
            return cls.parse_obj(data)
        except ValidationError as ex:
            error_msg = f"Encountered error parsing prefab: {data['name']}"
            _LOGGER.error(error_msg)
            _LOGGER.error(str(ex))


class GameObjectManager:
    """Manages GameObject and Component Data for a single World instance."""

    __slots__ = (
        "world",
        "_prefabs",
        "_component_metadata",
        "_component_data",
        "_gameobjects",
        "_dead_gameobjects",
    )

    world: World
    """The manager's associated World instance."""

    _component_data: esper.World
    """Esper ECS instance used for efficiency."""

    _gameobjects: Dict[int, GameObject]
    """Mapping of GameObjects to unique identifiers."""

    _prefabs: Dict[str, GameObjectPrefab]
    """GameObject prefab definitions indexed by name."""

    _component_metadata: Dict[str, ComponentInfo]
    """Metadata about components that have been registered with the ECS."""

    _dead_gameobjects: OrderedSet[int]
    """IDs of GameObjects to clean-up following destruction."""

    def __init__(self, world: World) -> None:
        self.world = world
        self._prefabs = {}
        self._component_metadata = {}
        self._gameobjects = {}
        self._component_data = esper.World()
        self._dead_gameobjects = OrderedSet([])

    @property
    def component_data(self) -> esper.World:
        return self._component_data

    def spawn_gameobject(
        self,
        components: Optional[Iterable[Component]] = None,
        name: Optional[str] = None,
    ) -> GameObject:
        """Create a new GameObject and add it to the world.

        Parameters
        ----------
        components
            A collection of component instances to add to the GameObject.
        name
            A name to give the GameObject.

        Returns
        -------
        GameObject
            The created GameObject.
        """
        components_to_add: Iterable[Component] = components if components else []

        entity_id = self.component_data.create_entity()

        gameobject = GameObject(
            unique_id=entity_id,
            world=self.world,
            name=(name if name else f"GameObject({entity_id})"),
        )

        self._gameobjects[gameobject.uid] = gameobject

        # Add components
        for c in components_to_add:
            self.component_data.add_component(gameobject.uid, c)

        # Call component on add methods
        for c in components_to_add:
            c.on_add(gameobject)

        gameobject.activate()

        return gameobject

    def instantiate_prefab(
        self, prefab_name: str, gameobject_name: Optional[str] = None
    ) -> GameObject:
        """Create a new GameObject from a prefab and add it to the world.

        Parameters
        ----------
        prefab_name
            The name of the prefab to use
        gameobject_name
            A name to assign to the gameobject

        Returns
        -------
        GameObject
            The created GameObject.
        """
        prefab = self._prefabs[prefab_name]
        gameobject = self.spawn_gameobject(name=gameobject_name)

        for component_name, component_data in self._resolve_components(prefab).items():
            try:
                component_factory = self.get_component_info(component_name).factory
            except KeyError:
                raise Exception(
                    f"Cannot find component, {component_name}. "
                    "Please ensure that this component has "
                    "been registered with the simulation's world instance "
                    f"using, 'sim.world.gameobject_manager.register_component({component_name})'."
                )

            gameobject.add_component(
                component_factory.create(self.world, **component_data)
            )

        for child in prefab.children:
            gameobject.add_child(self.instantiate_prefab(child))

        gameobject.name = prefab.name

        return gameobject

    def get_prefab(self, prefab_name: str) -> GameObjectPrefab:
        """Retrieve an entity prefab

        Parameters
        ----------
        prefab_name
            The name of the prefab
        """
        if prefab_name in self._prefabs:
            return self._prefabs[prefab_name]
        raise MissingPrefabError(prefab_name)

    def get_matching_prefabs(self, *patterns: str) -> List[GameObjectPrefab]:
        """
        Get all prefabs with names that match the given regex strings.

        Parameters
        ----------
        *patterns
            Glob-patterns of names to check for.

        Returns
        -------
        List[GameObjectPrefab]
            The names of prefabs in the table that match the pattern.
        """

        matches: List[GameObjectPrefab] = []

        for name, prefab in self._prefabs.items():
            if any([re.match(p, name) for p in patterns]):
                matches.append(prefab)

        return matches

    def add_prefab(self, prefab: GameObjectPrefab) -> None:
        """Add a prefab to the factory or overwrite an existing one.

        Parameters
        ----------
        prefab
            The prefab to add.
        """

        if prefab.name in self._prefabs and prefab.name in prefab.extends:
            # If this condition is true, then we assume
            # the user wants to extend and overwrite an existing prefab
            # So we load the existing prefab, update the values, and overwrite it
            existing_prefab = self._prefabs[prefab.name]

            # We need to remove the name from the extends list
            # to prevent an infinite loop when instantiating
            revised_extends_list = [n for n in prefab.extends if n != prefab.name]

            # Only overwrite the children if the new prefab specifies them
            children = (
                prefab.children if len(prefab.children) else existing_prefab.children
            )

            # Allow new components to completely overwrite old ones
            combined_components = {**existing_prefab.components, **prefab.components}

            combined_prefab = GameObjectPrefab(
                name=prefab.name,
                is_template=prefab.is_template,
                extends=revised_extends_list,
                components=combined_components,
                children=children,
                tags=existing_prefab.tags.union(prefab.tags),
                metadata={**existing_prefab.metadata, **prefab.metadata}
            )

            self._prefabs[prefab.name] = combined_prefab
        else:
            # Add the prefab to the dictionary and overwrite any existing
            # prefab with the same name
            self._prefabs[prefab.name] = prefab

    def _resolve_components(
        self, prefab: GameObjectPrefab
    ) -> Dict[str, Dict[str, Any]]:
        """Create the aggregate collection of components for a prefab and its templates.

        This function traverses the inheritance tree of prefabs and creates the final
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
            self._resolve_components(self.get_prefab(base)) for base in prefab.extends
        ]

        for entry in base_components:
            components.update(entry)

        components.update(prefab.components)

        return components

    def get_gameobject(self, gameobject_id: int) -> GameObject:
        """Get a GameObject.

        Parameters
        ----------
        gameobject_id
            The ID of the GameObject.

        Returns
        -------
        GameObject
            The GameObject with the given ID.
        """
        if gameobject_id in self._gameobjects:
            return self._gameobjects[gameobject_id]

        raise GameObjectNotFoundError(gameobject_id)

    def get_gameobjects(self) -> List[GameObject]:
        """Get all gameobjects.

        Returns
        -------
        List[GameObject]
            All the GameObjects that exist in the world.
        """
        return list(self._gameobjects.values())

    def has_gameobject(self, gameobject: GameObject) -> bool:
        """Check that a GameObject exists.

        Parameters
        ----------
        gameobject
            The GameObject to check for.

        Returns
        -------
        bool
            True if the GameObject exists. False otherwise.
        """
        return gameobject.uid in self._gameobjects

    def destroy_gameobject(self, gameobject: GameObject) -> None:
        """Remove a gameobject from the world.

        Parameters
        ----------
        gameobject
            The GameObject to remove.

        Note
        ----
        This component also removes all the components from the gameobject before destruction.
        """
        gameobject = self._gameobjects[gameobject.uid]

        self._dead_gameobjects.append(gameobject.uid)

        # Destroy all children first
        for child in gameobject.children:
            self.destroy_gameobject(child)

        # Destroy attached components
        attached_components = gameobject.get_components()

        for component in attached_components:
            component.on_remove(gameobject)

        for component in attached_components:
            self.component_data.remove_component(gameobject.uid, type(component))

    def add_component(self, gameobject: GameObject, component: Component) -> None:
        """Add a component to a GameObject.

        Parameters
        ----------
        gameobject
            The GameObject to add the component to.
        component
            The component instance to add.
        """
        self.component_data.add_component(gameobject.uid, component)
        component.on_add(gameobject)

    def remove_component(
        self, gameobject: GameObject, component_type: Type[Component]
    ) -> None:
        """Remove a component from a GameObject.

        Parameters
        ----------
        gameobject
            The GameObject to remove the component from.
        component_type
            The class type of the component to remove.
        """

        try:
            if not self.has_component(gameobject, component_type):
                return

            component = self.component_data.component_for_entity(
                gameobject.uid, component_type
            )
            component.on_remove(gameobject)
            self.component_data.remove_component(gameobject.uid, component_type)

        except KeyError:
            # Esper's ECS will throw a key error if the GameObject does not
            # have any components.
            return

    def get_component_for_gameobject(
        self, gameobject: GameObject, component_type: Type[_CT]
    ) -> _CT:
        """Return the component type attached to an entity

        Parameters
        ----------
        gameobject
            The GameObject to get the component from
        component_type
            The component type to retrieve

        Returns
        -------
        _CT
            The instance of the given component type
        """
        try:
            return self.component_data.component_for_entity(
                gameobject.uid, component_type
            )
        except KeyError:
            raise ComponentNotFoundError(component_type)

    def try_component_for_gameobject(
        self, gameobject: GameObject, component_type: Type[_CT]
    ) -> Optional[_CT]:
        """Attempt to get a component attached to a GameObject.

        Parameters
        ----------
        gameobject
            The GameObject to get the component from.
        component_type
            The component type to retrieve.

        Returns
        -------
        _CT or None
            The instance of the given component type
        """
        try:
            return self.component_data.try_component(gameobject.uid, component_type)
        except KeyError:
            return None

    def has_components(
        self, gameobject: GameObject, *component_types: Type[_CT]
    ) -> bool:
        """Check if a GameObject has one or more components.

        Parameters
        ----------
        gameobject
            The GameObject to check.
        *component_types
            The component types to check for.

        Returns
        -------
        bool
            True if the components are present of the GameObject, false otherwise.
        """
        try:
            return self.component_data.has_components(gameobject.uid, *component_types)
        except KeyError:
            return False

    def has_component(self, gameobject: GameObject, component_type: Type[_CT]) -> bool:
        """Check if a GameObject has a component.

        Parameters
        ----------
        gameobject
            The ID of the GameObject to check.
        component_type
            The component types to check for.

        Returns
        -------
        bool
            True if the component is present of the GameObject, false otherwise.
        """
        try:
            return self.component_data.has_component(gameobject.uid, component_type)
        except KeyError:
            return False

    def get_components_for_gameobject(
        self, gameobject: GameObject
    ) -> Tuple[Component, ...]:
        """Get all components associated with a GameObject.

        Parameters
        ----------
        gameobject
            The GameObject.

        Returns
        -------
        Tuple[Component, ...]
            A tuple containing all the component instances attached to this GameObject.
        """
        return self.component_data.components_for_entity(gameobject.uid)

    def clear_dead_gameobjects(self) -> None:
        """Delete gameobjects that were removed from the world."""
        for gameobject_id in self._dead_gameobjects:
            if len(self._gameobjects[gameobject_id].get_components()) > 0:
                self._component_data.delete_entity(gameobject_id, True)

            gameobject = self._gameobjects[gameobject_id]

            if gameobject.parent is not None:
                gameobject.parent.remove_child(gameobject)

            del self._gameobjects[gameobject_id]
        self._dead_gameobjects.clear()

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
        return self._component_metadata[component_name]

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
            The class of the component.
        name
            An alternative name used to reference the component in EntityPrefabs.
        factory
            A factory used to construct this component type.
        """
        component_name = name if name is not None else component_type.__name__

        self._component_metadata[component_name] = ComponentInfo(
            name=component_name,
            component_type=component_type,
            factory=(
                factory
                if factory is not None
                else DefaultComponentFactory(component_type)
            ),
        )

        component_type.on_register(self.world)

    def create_component(
        self, component_type: Union[str, Type[_CT]], **kwargs: Any
    ) -> _CT:
        """Register a component class type with the engine.

        Parameters
        ----------
        component_type
            The class of the component.
        **kwargs
            Keyword arguments to pass to the component's factory
        """
        component_name = (
            component_type
            if isinstance(component_type, str)
            else component_type.__name__
        )

        return cast(
            _CT,
            self._component_metadata[component_name].factory.create(
                self.world, **kwargs
            ),
        )


_T1 = TypeVar("_T1", bound=Component)
_T2 = TypeVar("_T2", bound=Component)
_T3 = TypeVar("_T3", bound=Component)
_T4 = TypeVar("_T4", bound=Component)
_T5 = TypeVar("_T5", bound=Component)
_T6 = TypeVar("_T6", bound=Component)
_T7 = TypeVar("_T7", bound=Component)
_T8 = TypeVar("_T8", bound=Component)


class World:
    """Manages Gameobjects, Systems, events, and resources."""

    __slots__ = (
        "_resource_manager",
        "_gameobject_manager",
        "_system_manager",
        "_event_manager",
    )

    _gameobject_manager: GameObjectManager
    """Manages GameObjects and Component data."""

    _resource_manager: ResourceManager
    """Global resources shared by systems in the ECS."""

    _system_manager: SystemManager
    """The systems run every simulation step."""

    _event_manager: EventManager
    """Manages event listeners."""

    def __init__(self) -> None:
        self._resource_manager = ResourceManager(self)
        self._system_manager = SystemManager(self)
        self._event_manager = EventManager(self)
        self._gameobject_manager = GameObjectManager(self)

    @property
    def system_manager(self) -> SystemManager:
        return self._system_manager

    @property
    def gameobject_manager(self) -> GameObjectManager:
        return self._gameobject_manager

    @property
    def resource_manager(self) -> ResourceManager:
        return self._resource_manager

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

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
        return self._gameobject_manager.component_data.get_component(component_type)  # type: ignore

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
            for uid, components in self._gameobject_manager.component_data.get_components(
                *component_types
            )
        ]

        # We have to ignore the type because of esper's lax type hinting for
        # world.get_components()
        return ret  # type: ignore

    def step(self) -> None:
        """Advance the simulation as single tick and call all the systems."""
        self._gameobject_manager.clear_dead_gameobjects()
        self._system_manager.update_systems()
