# pylint: disable=C0302
"""Entity Component System

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
import logging
from abc import ABC, abstractmethod
from queue import PriorityQueue
from typing import (
    Any,
    Callable,
    ClassVar,
    Iterable,
    Iterator,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

import esper
from ordered_set import OrderedSet

_LOGGER = logging.getLogger(__name__)

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")
_ST = TypeVar("_ST", bound="ISystem")


class ResourceNotFoundError(Exception):
    """Exception raised when attempting to access a resource that does not exist."""

    __slots__ = ("resource_type", "message")

    resource_type: Type[Any]
    """The class type of the resource."""
    message: str
    """An error message."""

    def __init__(self, resource_type: Type[Any]) -> None:
        """
        Parameters
        ----------
        resource_type
            The type of the resource not found.
        """
        super().__init__()
        self.resource_type = resource_type
        self.message = f"Could not find resource with type: {resource_type.__name__}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(resource_type={self.resource_type})"


class SystemNotFoundError(Exception):
    """Exception raised when attempting to access a system that does not exist."""

    __slots__ = ("system_type", "message")

    system_type: str
    """The class type of the system."""
    message: str
    """An error message."""

    def __init__(self, system_type: str) -> None:
        """
        Parameters
        ----------
        system_type
            The type of the resource not found.
        """
        super().__init__()
        self.system_type = system_type
        self.message = f"Could not find system with type: {system_type}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(resource_type={self.system_type})"


class GameObjectNotFoundError(Exception):
    """Exception raised when attempting to access a GameObject that does not exist."""

    __slots__ = ("gameobject_id", "message")

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
        return f"{self.__class__.__name__}(gameobject_uid={self.gameobject_id})"


class ComponentNotFoundError(Exception):
    """Exception raised when attempting to access a component that does not exist."""

    __slots__ = ("component_type", "message")

    component_type: Type[Component]
    """The type of component not found."""
    message: str
    """An error message."""

    def __init__(self, component_type: Type[Component]) -> None:
        """
        Parameters
        ----------
        component_type
            The desired component type.
        """
        super().__init__()
        self.component_type = component_type
        self.message = f"Could not find Component with type: {component_type.__name__}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(component={self.component_type.__name__})"


class Event:
    """Events signal when things happen in the simulation."""

    __slots__ = ("_world", "_event_type", "data")

    _world: World
    """The world instance to fire this event on."""
    _event_type: str
    """The ID of this event."""
    data: dict[str, Any]
    """General metadata."""

    def __init__(self, event_type: str, world: World, **kwargs: Any) -> None:
        self._world = world
        self._event_type = event_type
        self.data = {**kwargs}

    @property
    def world(self) -> World:
        """The world instance to fire this event on."""
        return self._world

    @property
    def event_type(self) -> str:
        """The type name for the event."""
        return self._event_type

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a JSON-compliant dict."""
        return {"event_id": self.event_type, "data": self.data}


class GameObject:
    """A reference to an entity within the world.

    GameObjects wrap a unique integer identifier and provide an interface to access
    associated components and child/parent gameobjects.
    """

    __slots__ = (
        "_uid",
        "_name",
        "world",
        "children",
        "parent",
        "metadata",
        "_component_types",
        "_component_manager",
        "_event_listeners",
    )

    _uid: int
    """The unique ID of this GameObject."""
    _name: str
    """The name of this GameObject."""
    world: World
    """The world instance a GameObject belongs to."""
    _component_manager: esper.World
    """Reference to Esper ECS instance with all the component data."""
    children: list[GameObject]
    """Child GameObjects below this one in the hierarchy."""
    parent: Optional[GameObject]
    """The parent GameObject that this GameObject is a child of."""
    metadata: dict[str, Any]
    """Metadata associated with this GameObject."""
    _component_types: list[Type[Component]]
    """Types of the GameObjects components in order of addition."""
    _event_listeners: dict[str, OrderedSet[Callable[[Event], None]]]
    """Event listeners that are only called when a specific type of event fires."""

    def __init__(
        self,
        unique_id: int,
        world: World,
        component_manager: esper.World,
        name: str = "",
    ) -> None:
        self._uid = unique_id
        self._name = name if name else f"GameObject({unique_id})"
        self.world = world
        self._component_manager = component_manager
        self.parent = None
        self.children = []
        self.metadata = {}
        self._component_types = []
        self._event_listeners = {}

    @property
    def uid(self) -> int:
        """A GameObject's ID."""
        return self._uid

    @property
    def exists(self) -> bool:
        """Check if the GameObject still exists in the ECS.

        Returns
        -------
        bool
            True if the GameObject exists, False otherwise.
        """
        return self.world.gameobject_manager.has_gameobject(self.uid)

    @property
    def is_active(self) -> bool:
        """Check if a GameObject is active."""
        return self.has_component(Active)

    @property
    def name(self) -> str:
        """Get the GameObject's name"""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the GameObject's name"""
        self._name = f"{value}({self.uid})"

    def activate(self) -> None:
        """Tag the GameObject as active."""
        self.add_component(Active())

        for child in self.children:
            child.activate()

        self.dispatch_event(Event("activated", world=self.world, gameobject=self))

    def deactivate(self) -> None:
        """Remove the Active tag from a GameObject."""

        self.remove_component(Active)

        for child in self.children:
            child.deactivate()

        self.dispatch_event(Event("deactivated", world=self.world, gameobject=self))

    def get_components(self) -> tuple[Component, ...]:
        """Get all components associated with the GameObject.

        Returns
        -------
        tuple[Component, ...]
            Component instances
        """
        try:
            return self._component_manager.components_for_entity(self.uid)
        except KeyError:
            # Ignore errors if gameobject is not found in esper ecs
            return ()

    def get_component_types(self) -> tuple[Type[Component], ...]:
        """Get the class types of all components attached to the GameObject.

        Returns
        -------
        tuple[Type[Component], ...]
            Collection of component types.
        """
        return tuple(self._component_types)

    def add_component(self, component: _CT) -> _CT:
        """Add a component to this GameObject.

        Parameters
        ----------
        component
            The component.

        Returns
        -------
        _CT
            The added component
        """

        if self.has_component(type(component)):
            raise TypeError(
                "Cannot have multiple components of same type. "
                f"Attempted to add {type(component)}."
            )

        component.gameobject = self
        self._component_manager.add_component(self.uid, component)
        self._component_types.append(type(component))
        component.on_add()

        return component

    def add_event_listener(
        self,
        event_name: str,
        listener: Callable[[Event], None],
    ) -> None:
        """Register a listener function to a specific event type.

        Parameters
        ----------
        listener
            A function to be called when the given event type fires.
        """
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = OrderedSet([])

        listener_set = self._event_listeners[event_name]
        listener_set.add(listener)

    def remove_event_listener(
        self, event_name: str, listener: Callable[[Event], None]
    ) -> None:
        """Remove a listener function from a specific event type.

        Parameters
        ----------
        event_name : str
            The type of event to remove the listener from.
        callback : Callable[[Event], None]
            The callback function to be removed.
        """
        if event_name in self._event_listeners:
            listener_set = self._event_listeners[event_name]
            listener_set.discard(listener)

    def remove_all_event_listeners_for_event(self, event_name: str) -> None:
        """Remove all event listeners for a specific event type.

        Parameters
        ----------
        event_name : str
            The type of event to remove listeners for.
        """
        if event_name in self._event_listeners:
            del self._event_listeners[event_name]

    def remove_all_event_listeners(self) -> None:
        """Remove all event listeners associated with this GameObject."""
        self._event_listeners.clear()

    def dispatch_event(self, event: Event) -> None:
        """Fire an event and trigger associated event listeners.

        Parameters
        ----------
        event : Event
            The event to fire
        """
        for callback_fn in self._event_listeners.get(event.event_type, OrderedSet([])):
            callback_fn(event)

    def remove_component(self, component_type: Type[Component]) -> bool:
        """Remove a component from the GameObject.

        Parameters
        ----------
        component_type
            The type of the component to remove.

        Returns
        -------
        bool
            Returns True if component is removed, False otherwise.
        """
        try:
            if not self.has_component(component_type):
                return False

            component = self.get_component(component_type)
            component.on_remove()
            self._component_types.remove(type(component))
            self._component_manager.remove_component(self.uid, component_type)
            return True

        except KeyError:
            # Esper's ECS will throw a key error if the GameObject does not
            # have any components.
            return False

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
        try:
            return self._component_manager.component_for_entity(
                self.uid, component_type
            )
        except KeyError as exc:
            raise ComponentNotFoundError(component_type) from exc

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
        try:
            return self._component_manager.has_components(self.uid, *component_types)
        except KeyError:
            return False

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
        try:
            return self._component_manager.has_component(self.uid, component_type)
        except KeyError:
            return False

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
            return self._component_manager.try_component(self.uid, component_type)
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

    def get_component_in_child(self, component_type: Type[_CT]) -> tuple[int, _CT]:
        """Get a single instance of a component type attached to a child.

        Parameters
        ----------
        component_type
            The class type of the component.

        Returns
        -------
        tuple[int, _CT]
            A tuple containing the ID of the child and an instance of the component.

        Notes
        -----
        Performs a depth-first search of the children and their children and
        returns the first instance of the component type.
        """

        stack: list[GameObject] = list(*self.children)
        checked: set[GameObject] = set()

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
    ) -> list[tuple[int, _CT]]:
        """Get all the instances of a component attached to children of a GameObject.

        Parameters
        ----------
        component_type
            The class type of the component

        Returns
        -------
        list[tuple[int, _CT]]
            A list containing tuples with the ID of the children and the instance of the
            component.
        """
        results: list[tuple[int, _CT]] = []

        stack: list[GameObject] = list(*self.children)
        checked: set[GameObject] = set()

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

    def to_dict(self) -> dict[str, Any]:
        """Serialize the GameObject to a dict.

        Returns
        -------
        dict[str, Any]
            A dict containing the relevant fields serialized for JSON.
        """
        ret = {
            "id": self.uid,
            "name": self.name,
            "active": self.has_component(Active),
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
        return False

    def __int__(self) -> int:
        return self.uid

    def __hash__(self) -> int:
        return self.uid

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"GameObject(id={self.uid!r}, name={self.name!r})"


class Component(ABC):
    """A collection of data attributes associated with a GameObject."""

    __slots__ = ("_gameobject",)

    _gameobject: GameObject
    """The GameObject the component belongs to."""

    @property
    def gameobject(self) -> GameObject:
        """Get the GameObject instance for this component."""
        return self._gameobject

    @gameobject.setter
    def gameobject(self, value: GameObject) -> None:
        """Set the GameObject instance."""
        # This method should only be called by the ECS
        if not hasattr(self, "_gameobject"):
            self._gameobject = value
        else:
            raise RuntimeError("Cannot reassign the GameObject for a component")

    def on_add(self) -> None:
        """Lifecycle method called when the component is added to a GameObject."""
        return

    def on_remove(self) -> None:
        """Lifecycle method called when the component is removed from a GameObject."""
        return

    def to_dict(self) -> dict[str, Any]:
        """Serialize the component to a JSON-serializable dictionary."""
        return {}


class TagComponent(Component):
    """An Empty component used to mark a GameObject as having a state or type."""

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def to_dict(self) -> dict[str, Any]:
        return {}


class Active(TagComponent):
    """Tags a GameObject as active within the simulation."""


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
    def on_add(self, world: World) -> None:
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
        """Lifecycle method called after a system updates.

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


class System(ISystem, ABC):
    """Base class for systems, providing implementation for most lifecycle methods."""

    __system_group__: ClassVar[str] = "UpdateSystems"
    """The system group the system will be added to."""
    __update_order__: ClassVar[tuple[str, ...]] = ()
    """Ordering constraints for when the system should be update."""

    __slots__ = ("_active",)

    _active: bool
    """Will this system update during the next simulation step."""

    def __init__(self) -> None:
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

    def on_add(self, world: World) -> None:
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
        """Lifecycle method called after a system updates.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        return

    def should_run_system(self, world: World) -> bool:
        """Checks if this system should run this simulation step."""
        return self._active

    @classmethod
    def system_name(cls) -> str:
        return cls.__name__

    @classmethod
    def system_group(cls) -> str:
        return cls.__system_group__

    @classmethod
    def update_order(cls) -> tuple[str, ...]:
        return cls.__update_order__


@dataclasses.dataclass
class _SystemSortNode:

    system: System
    update_first: bool = False
    update_last: bool = False
    order: int = 0


@dataclasses.dataclass(order=True)
class _NodeQueueEntry:
    priority: int
    item: _SystemSortNode = dataclasses.field(compare=False)


def _topological_sort(systems: list[System]) -> list[System]:
    """Perform topological sort on the provided systems."""

    # Convert the systems to nodes
    nodes: dict[str, _SystemSortNode] = {}
    edges: list[tuple[str, str]] = []
    for system in systems:
        node = _SystemSortNode(system=system)

        for constraint in system.update_order():
            if constraint == "first":
                node.update_first = True
                node.order -= 1
            elif constraint == "last":
                node.update_last = True
                node.order += 1
            else:
                # We have to parse it
                command, system_name = tuple(s.strip() for s in constraint.split(":"))

                if command == "before":
                    edges.append((system.system_name(), system_name))
                elif command == "after":
                    edges.append((system_name, system.system_name()))
                else:
                    raise ValueError(f"Unknown update order constraint: {constraint}.")

        if node.update_first and node.update_last:
            raise ValueError(
                f"'{system.system_name()}' has constraints to update first and last."
            )

        nodes[system.system_name()] = node

    # verify all edges have nodes
    for _n, _m in edges:
        if _n not in nodes:
            raise KeyError(f"Missing System with name: {_n}.")
        if _m not in nodes:
            raise KeyError(f"Missing System with name: {_m}.")

    def get_incoming_edges(_node: _SystemSortNode) -> list[str]:
        return [_n for _n, _m in edges if _m == _node.system.system_name()]

    def get_outgoing_edges(_node: _SystemSortNode) -> list[str]:
        return [_m for _n, _m in edges if _n == _node.system.system_name()]

    result: list[System] = []

    # Get all nodes with no incoming edges.
    starting_nodes = [
        node for node in nodes.values() if len(get_incoming_edges(node)) == 0
    ]

    node_queue: PriorityQueue[_NodeQueueEntry] = PriorityQueue()
    for node in starting_nodes:
        node_queue.put(_NodeQueueEntry(priority=node.order, item=node))

    while not node_queue.empty():
        entry = node_queue.get()
        node = entry.item
        result.append(node.system)

        for dependent_name in get_outgoing_edges(node):
            dependent = nodes[dependent_name]
            edges.remove((node.system.system_name(), dependent_name))

            if len(get_incoming_edges(dependent)) == 0:
                node_queue.put(
                    _NodeQueueEntry(priority=dependent.order, item=dependent)
                )

    if edges:
        raise ValueError(f"Systems ordering contains a dependency cycle.")

    return result


class SystemGroup(System, ABC):
    """A group of ECS systems that run as a unit.

    SystemGroups allow users to better structure the execution order of their systems.
    """

    __slots__ = ("_children",)

    _children: list[System]
    """The systems that belong to this group"""

    def __init__(self) -> None:
        super().__init__()
        self._children = []

    def set_active(self, value: bool) -> None:
        super().set_active(value)
        for child in self._children:
            child.set_active(value)

    def iter_children(self) -> Iterator[System]:
        """Get an iterator for the group's children.

        Returns
        -------
        Iterator[System]
            An iterator for the child system collection.
        """
        return iter(self._children)

    def add_child(self, system: System) -> None:
        """Add a new system as a sub_system of this group.

        Parameters
        ----------
        system
            The system to add to this group.
        """
        self._children.append(system)

    def remove_child(self, system_type: Type[System]) -> None:
        """Remove a child system.

        If for some reason there are more than one instance of the given system type,
        this method will remove the first instance it finds.

        Parameters
        ----------
        system_type
            The class type of the system to remove.
        """
        children_to_remove = [
            child for child in self._children if isinstance(child, system_type)
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
        for child in self._children:
            child.on_start_running(world)
            if child.should_run_system(world):
                child.on_update(world)
            child.on_stop_running(world)

    def sort_children(self) -> None:
        """Performs topologically sort child systems."""
        self._children = _topological_sort(self._children)

        for child in self._children:
            if isinstance(child, SystemGroup):
                child.sort_children()


class InitializationSystems(SystemGroup):
    """A group of systems that run once at the beginning of the simulation.

    Any content initialization systems or initial world building systems should
    belong to this group.
    """

    __system_group__ = "SystemManager"
    __update_order__ = ("before:EarlyUpdateSystems", "first")

    def on_update(self, world: World) -> None:
        # Run all child systems first before deactivating
        super().on_update(world)
        self.set_active(False)


class EarlyUpdateSystems(SystemGroup):
    """The early phase of the update loop."""

    __system_group__ = "SystemManager"
    __update_order__ = ("before:UpdateSystems",)


class UpdateSystems(SystemGroup):
    """The main phase of the update loop."""

    __system_group__ = "SystemManager"
    __update_order__ = ("before:LateUpdateSystems",)


class LateUpdateSystems(SystemGroup):
    """The late phase of the update loop."""

    __system_group__ = "SystemManager"
    __update_order__ = ("last",)


class SystemManager(SystemGroup):
    """Manages system instances for a single world instance."""

    __slots__ = ("_world",)

    _world: World
    """The world instance associated with the SystemManager."""

    def __init__(self, world: World) -> None:
        super().__init__()
        self._world = world

    def add_system(
        self,
        system: System,
    ) -> None:
        """Add a System instance.

        Parameters
        ----------
        system
            The system to add.
        """

        stack: list[SystemGroup] = [self]

        while stack:
            current_sys = stack.pop()

            if current_sys.system_name() == system.system_group():
                current_sys.add_child(system)
                return

            for child in current_sys.iter_children():
                if isinstance(child, SystemGroup):
                    stack.append(child)

        raise SystemNotFoundError(system.system_group())

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
        stack: list[tuple[SystemGroup, System]] = [
            (self, child) for child in self._children
        ]

        while stack:
            _, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                return current_sys

            if isinstance(current_sys, SystemGroup):
                for child in current_sys.iter_children():
                    stack.append((current_sys, child))

        raise SystemNotFoundError(system_type.__name__)

    def remove_system(self, system_type: Type[System]) -> None:
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

        stack: list[tuple[SystemGroup, System]] = [
            (self, c) for c in self.iter_children()
        ]

        while stack:
            group, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                group.remove_child(system_type)
                current_sys.on_destroy(self._world)

            else:
                if isinstance(current_sys, SystemGroup):
                    for child in current_sys.iter_children():
                        stack.append((current_sys, child))

    def update_systems(self) -> None:
        """Update all systems in the manager."""
        self.on_update(self._world)


class ResourceManager:
    """Manages shared resources for a world instance."""

    __slots__ = ("_resources", "_world")

    _world: World
    """The world instance associated with the SystemManager."""
    _resources: dict[Type[Any], Any]
    """Resources shared by the world instance."""

    def __init__(self, world: World) -> None:
        self._world = world
        self._resources = {}

    @property
    def resources(self) -> Iterable[Any]:
        """Get an iterable of all the current resources."""
        return self._resources.values()

    def add_resource(self, resource: Any) -> None:
        """Add a shared resource to a world.

        Parameters
        ----------
        resource
            The resource to add
        """
        resource_type = type(resource)  # type: ignore
        if resource_type in self._resources:
            _LOGGER.warning("Replacing existing resource of type: %s", resource_type)  # type: ignore
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
        except KeyError as exc:
            raise ResourceNotFoundError(resource_type) from exc

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
        except KeyError as exc:
            raise ResourceNotFoundError(resource_type) from exc

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


class EventManager:
    """Manages event listeners for a single World instance."""

    __slots__ = (
        "_general_event_listeners",
        "_event_listeners_by_type",
        "_world",
    )

    _world: World
    """The world instance associated with the SystemManager."""
    _general_event_listeners: OrderedSet[Callable[[Event], None]]
    """Event listeners that are called when any event fires."""
    _event_listeners_by_type: dict[str, OrderedSet[Callable[[Event], None]]]
    """Event listeners that are only called when a specific type of event fires."""

    def __init__(self, world: World) -> None:
        self._world = world
        self._general_event_listeners = OrderedSet([])
        self._event_listeners_by_type = {}

    def on_event(
        self,
        event_type: str,
        listener: Callable[[Event], None],
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
        listener_set = self._event_listeners_by_type[event_type]
        listener_set.add(listener)

    def on_any_event(self, listener: Callable[[Event], None]) -> None:
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
            event.event_type, OrderedSet([])
        ):
            callback_fn(event)

        for callback_fn in self._general_event_listeners:
            callback_fn(event)


class ComponentFactory(ABC):
    """Creates instances of a component class."""

    __component__: ClassVar[str] = ""

    def __init__(self) -> None:
        super().__init__()
        if not self.__component__:
            raise ValueError(
                f"Missing '__component__' class attribute for {type(self)}."
            )

    @property
    def component_type(self) -> str:
        """The class name of the component this constructs"""
        return self.__component__

    @abstractmethod
    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        """Create an instance of the component."""

        raise NotImplementedError()


class GameObjectManager:
    """Manages GameObject and Component Data for a single World instance."""

    __slots__ = (
        "world",
        "component_factories",
        "_component_manager",
        "_gameobjects",
        "_dead_gameobjects",
    )

    world: World
    """The manager's associated World instance."""
    component_factories: dict[str, ComponentFactory]
    """Component class names mapped to factory instances."""
    _component_manager: esper.World
    """Esper ECS instance used for efficiency."""
    _gameobjects: dict[int, GameObject]
    """Mapping of GameObjects to unique identifiers."""
    _dead_gameobjects: OrderedSet[int]
    """IDs of GameObjects to clean-up following destruction."""

    def __init__(self, world: World) -> None:
        self.world = world
        self._gameobjects = {}
        self._component_manager = esper.World()
        self._dead_gameobjects = OrderedSet([])
        self.component_factories = {}

    @property
    def component_manager(self) -> esper.World:
        """Get the esper world instance with all the component data."""
        return self._component_manager

    @property
    def gameobjects(self) -> Iterable[GameObject]:
        """Get all gameobjects.

        Returns
        -------
        list[GameObject]
            All the GameObjects that exist in the world.
        """
        return self._gameobjects.values()

    def add_component_factory(self, factory: ComponentFactory) -> None:
        """Register a component type with the ECS."""

        self.component_factories[factory.component_type] = factory

    def spawn_gameobject(
        self,
        components: Optional[dict[str, dict[str, Any]]] = None,
        name: str = "",
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
        entity_id = self._component_manager.create_entity()

        gameobject = GameObject(
            unique_id=entity_id,
            world=self.world,
            component_manager=self._component_manager,
            name=name,
        )

        self._gameobjects[gameobject.uid] = gameobject

        if components:
            for component_type, factory_args in components.items():

                component = self.world.gameobjects.component_factories[
                    component_type
                ].instantiate(self.world, **factory_args)

                gameobject.add_component(component)

        gameobject.activate()

        return gameobject

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

    def has_gameobject(self, gameobject_id: int) -> bool:
        """Check that a GameObject exists.

        Parameters
        ----------
        gameobject_id
            The UID of the GameObject to check for.

        Returns
        -------
        bool
            True if the GameObject exists. False otherwise.
        """
        return gameobject_id in self._gameobjects

    def destroy_gameobject(self, gameobject: GameObject) -> None:
        """Remove a gameobject from the world.

        Parameters
        ----------
        gameobject
            The GameObject to remove.

        Note
        ----
        This component also removes all the components from the gameobject before
        destruction.
        """
        gameobject = self._gameobjects[gameobject.uid]

        self._dead_gameobjects.append(gameobject.uid)

        # Deactivate first
        gameobject.deactivate()
        gameobject.dispatch_event(
            Event("destroyed", world=self.world, gameobject=gameobject)
        )

        # Destroy all children
        for child in gameobject.children:
            self.destroy_gameobject(child)

        # Destroy attached components
        for component_type in reversed(gameobject.get_component_types()):
            gameobject.remove_component(component_type)

    def clear_dead_gameobjects(self) -> None:
        """Delete gameobjects that were removed from the world."""
        for gameobject_id in self._dead_gameobjects:
            if len(self._gameobjects[gameobject_id].get_components()) > 0:
                self._component_manager.delete_entity(gameobject_id, True)

            gameobject = self._gameobjects[gameobject_id]

            if gameobject.parent is not None:
                gameobject.parent.remove_child(gameobject)

            del self._gameobjects[gameobject_id]
        self._dead_gameobjects.clear()


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
        "resources",
        "gameobjects",
        "systems",
        "events",
    )

    gameobjects: GameObjectManager
    """Manages GameObjects and Component data."""
    resources: ResourceManager
    """Global resources shared by systems in the ECS."""
    systems: SystemManager
    """The systems run every simulation step."""
    events: EventManager
    """Manages event listeners."""

    def __init__(self) -> None:
        self.resources = ResourceManager(self)
        self.systems = SystemManager(self)
        self.events = EventManager(self)
        self.gameobjects = GameObjectManager(self)
        self.system_manager.add_system(InitializationSystems())
        self.system_manager.add_system(EarlyUpdateSystems())
        self.system_manager.add_system(UpdateSystems())
        self.system_manager.add_system(LateUpdateSystems())

    @property
    def system_manager(self) -> SystemManager:
        """Get the world's system manager."""
        return self.systems

    @property
    def gameobject_manager(self) -> GameObjectManager:
        """Get the world's gameobject manager"""
        return self.gameobjects

    @property
    def resource_manager(self) -> ResourceManager:
        """Get the world's resource manager"""
        return self.resources

    @property
    def event_manager(self) -> EventManager:
        """Get the world's event manager."""
        return self.events

    def get_component(self, component_type: Type[_CT]) -> list[tuple[int, _CT]]:
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
        return self.gameobjects.component_manager.get_component(  # type: ignore
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
        ret = self.gameobjects.component_manager.get_components(*component_types)

        # We have to ignore the type because of esper's lax type hinting for
        # world.get_components()
        return ret  # type: ignore

    def step(self) -> None:
        """Advance the simulation as single tick and call all the systems."""
        self.gameobjects.clear_dead_gameobjects()
        self.systems.update_systems()
