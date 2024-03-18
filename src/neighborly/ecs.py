"""Neighborly Entity Component System

This ECS implementation blends Unity-style GameObjects with a classic data-driven
modeling design. This ECS implementation is not thread-safe. It assumes that
everything happens sequentially on the same thread.

References:

- https://docs.unity3d.com/ScriptReference/GameObject.html
- https://github.com/benmoran56/esper
- https://github.com/bevyengine/bevy
- https://bevy-cheatbook.github.io/programming/change-detection.html
- https://bevy-cheatbook.github.io/programming/removal-detection.html
- https://docs.unity3d.com/Packages/com.unity.entities@0.1/manual/index.html

"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

import attrs
import esper
from ordered_set import OrderedSet

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")
_ST = TypeVar("_ST", bound="ISystem")


class Component(ABC):
    """A collection of data attributes associated with a GameObject."""

    __slots__ = ("_gameobject", "_has_gameobject")

    _gameobject: GameObject
    """The GameObject the component belongs to."""
    # We need an additional variable to track if the gameobject has been set because
    # the variable will be initialized outside the __init__ method, and we need to
    # ensure that it is not set again
    _has_gameobject: bool
    """Is the Component's _gameobject field set."""

    def __init__(self) -> None:
        super().__init__()
        self._has_gameobject = False

    @property
    def gameobject(self) -> GameObject:
        """Get the GameObject instance for this component."""
        return self._gameobject

    @gameobject.setter
    def gameobject(self, value: GameObject) -> None:
        """Sets the component's gameobject reference.

        Notes
        -----
        This setter should only be called internally by the ECS when adding new
        components to gameobjects. Calling this function twice will result in a
        RuntimeError.
        """
        if self._has_gameobject is True:
            raise RuntimeError("Cannot reassign a component to another GameObject.")
        self._gameobject = value

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize the component to a JSON-serializable dictionary."""
        return {}


class TagComponent(Component):
    """Tags a GameObject as active within the simulation."""

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def to_dict(self) -> dict[str, Any]:
        return {}


class Active(TagComponent):
    """Tags a GameObject as active within the simulation."""


class GameObject:
    """A reference to an entity within the world.

    GameObjects wrap a unique integer identifier and provide an interface to access
    associated components and child/parent gameobjects.
    """

    __slots__ = (
        "_id",
        "_name",
        "_world",
        "children",
        "parent",
        "_metadata",
        "_component_types",
        "_component_manager",
    )

    _id: int
    """A GameObject's unique ID."""
    _world: World
    """The world instance a GameObject belongs to."""
    _component_manager: esper.World
    """Reference to Esper ECS instance with all the component data."""
    _name: str
    """The name of the GameObject."""
    children: list[GameObject]
    """Child GameObjects below this one in the hierarchy."""
    parent: Optional[GameObject]
    """The parent GameObject that this GameObject is a child of."""
    _metadata: dict[str, Any]
    """Metadata associated with this GameObject."""
    _component_types: list[Type[Component]]
    """Types of the GameObjects components in order of addition."""

    def __init__(
        self,
        unique_id: int,
        world: World,
        component_manager: esper.World,
        name: str = "",
    ) -> None:
        self._id = unique_id
        self._world = world
        self._component_manager = component_manager
        self.parent = None
        self.children = []
        self._metadata = {}
        self._component_types = []
        self.name = name if name else "GameObject"

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
        return self.world.gameobjects.has_gameobject(self.uid)

    @property
    def is_active(self) -> bool:
        """Check if a GameObject is active."""
        return self.has_component(Active)

    @property
    def metadata(self) -> dict[str, Any]:
        """Get the metadata associated with this GameObject."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get the GameObject's name"""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the GameObject's name"""
        self._name = value

    def activate(self) -> None:
        """Tag the GameObject as active."""
        self.add_component(Active())

        for child in self.children:
            child.activate()

    def deactivate(self) -> None:
        """Remove the Active tag from a GameObject."""

        self.remove_component(Active)

        for child in self.children:
            child.deactivate()

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

    def add_component(self, component: Component) -> None:
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
        component.gameobject = self
        self._component_manager.add_component(self.uid, component)
        self._component_types.append(type(component))

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
            raise KeyError(
                f"Could not find Component with type: {component_type.__name__!r}."
            ) from exc

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

        raise KeyError(
            f"Could not find Component with type: {component_type.__name__!r}."
        )

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
        self.world.gameobjects.destroy_gameobject(self)

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
        return self._id

    def __hash__(self) -> int:
        return self._id

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.uid}, name={self.name})"


class GameObjectManager:
    """Manages GameObject and Component Data for a single World instance."""

    __slots__ = (
        "world",
        "_component_manager",
        "_gameobjects",
        "_dead_gameobjects",
    )

    world: World
    """The manager's associated World instance."""
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

    def spawn_gameobject(
        self,
        components: Optional[list[Component]] = None,
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
            for component in components:
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

        raise KeyError(f"Could not find GameObject with ID: {gameobject_id!r}.")

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


class ResourceManager:
    """Manages shared resources for a world instance."""

    __slots__ = ("_resources",)

    _resources: dict[Type[Any], Any]
    """Resources shared by the world instance."""

    def __init__(self) -> None:
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
        resource_type = type(resource)
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
            raise KeyError(
                f"Could not find resource with type: {resource_type.__name__!r}."
            ) from exc

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
            raise KeyError(
                f"Could not find resource with type: {resource_type.__name__!r}."
            ) from exc

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


class SystemGroup(System, ABC):
    """A group of ECS systems that run as a unit.

    SystemGroups allow users to better structure the execution order of their systems.
    """

    __slots__ = ("_children",)

    _children: list[tuple[int, System]]
    """The systems that belong to this group"""

    def __init__(self) -> None:
        super().__init__()
        self._children = []

    def set_active(self, value: bool) -> None:
        super().set_active(value)
        for _, child in self._children:
            child.set_active(value)

    def iter_children(self) -> Iterator[tuple[int, System]]:
        """Get an iterator for the group's children.

        Returns
        -------
        Iterator[tuple[SystemBase]]
            An iterator for the child system collection.
        """
        return iter(self._children)

    def add_child(self, system: System, priority: int = 0) -> None:
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
            pair for pair in self._children if isinstance(pair[1], system_type)
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

    __slots__ = ("_world",)

    _world: World
    """The world instance associated with the SystemManager."""

    def __init__(self, world: World) -> None:
        super().__init__()
        self._world = world

    def add_system(
        self,
        system: System,
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
                system.on_add(self._world)
                return

            if isinstance(current_sys, SystemGroup):
                for _, child in current_sys.iter_children():
                    stack.append(child)

        raise KeyError(f"Could not find system with type: {system_group.__name__!r}.")

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
            (self, child) for _, child in self._children
        ]

        while stack:
            _, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                return current_sys

            if isinstance(current_sys, SystemGroup):
                for _, child in current_sys.iter_children():
                    stack.append((current_sys, child))

        raise KeyError(f"Could not find system with type: {system_type.__name__!r}.")

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
            (self, c) for _, c in self.iter_children()
        ]

        while stack:
            group, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                group.remove_child(system_type)
                current_sys.on_destroy(self._world)

            else:
                if isinstance(current_sys, SystemGroup):
                    for _, child in current_sys.iter_children():
                        stack.append((current_sys, child))

    def update_systems(self) -> None:
        """Update all systems in the manager."""
        self.on_update(self._world)


@attrs.define(slots=True, kw_only=True)
class Event:
    """A signal that something has happened in the simulation."""

    __event_id__: ClassVar[str] = ""

    data: dict[str, Any] = attrs.field(factory=dict)
    """The name of this event."""

    @property
    def event_id(self) -> str:
        """The ID of the event."""
        return self.__event_id__ if self.__event_id__ else self.__class__.__name__


_T = TypeVar("_T", bound=Event)


class EventEmitter(Generic[_T]):
    """Emits events that observers can listen for."""

    __slots__ = ("listeners",)

    listeners: list[Callable[[object, _T], None]]

    def __init__(self) -> None:
        super().__init__()
        self.listeners = []

    def add_listener(
        self,
        listener: Callable[[object, _T], None],
    ) -> None:
        """Register a listener function to a specific event type.

        Parameters
        ----------
        listener
            A function to be called when the given event type fires.
        """
        self.listeners.append(listener)

    def remove_listener(
        self,
        listener: Callable[[object, _T], None],
    ) -> None:
        """Remove a listener from an event type.

        Parameters
        ----------
        listener
            A listener callback.
        """
        self.listeners.remove(listener)

    def remove_all_listeners(self) -> None:
        """Remove all listeners from an event.

        Parameters
        ----------
        event_name
            The name of the event.
        """
        self.listeners.clear()

    def dispatch(self, source: object, event: _T) -> None:
        """Fire an event and trigger associated event listeners.

        Parameters
        ----------
        source
            The source of the event
        event
            The event to fire
        """

        for callback_fn in self.listeners:
            callback_fn(source, event)


class EventManager:
    """Manages event listeners for a single World instance."""

    __slots__ = ("_event_listeners_by_type",)

    _event_listeners_by_type: defaultdict[str, OrderedSet[Callable[[Event], None]]]
    """Event listeners that are only called when a specific type of event fires."""

    def __init__(self) -> None:
        self._event_listeners_by_type = defaultdict(OrderedSet)

    def add_listener(
        self,
        event_name: str,
        listener: Callable[[Event], None],
    ) -> None:
        """Register a listener function to a specific event type.

        Parameters
        ----------
        event_name
            The name of the event.
        listener
            A function to be called when the given event type fires.
        """
        self._event_listeners_by_type[event_name].add(listener)

    def remove_listener(
        self,
        event_name: str,
        listener: Callable[[Event], None],
    ) -> None:
        """Remove a listener from an event type.

        Parameters
        ----------
        event_name
            The name of the event.
        listener
            A listener callback.
        """
        self._event_listeners_by_type[event_name].remove(listener)

    def remove_all_listeners(self, event_name: str) -> None:
        """Remove all listeners from an event.

        Parameters
        ----------
        event_name
            The name of the event.
        """
        del self._event_listeners_by_type[event_name]

    def dispatch_event(self, event: Event) -> None:
        """Fire an event and trigger associated event listeners.

        Parameters
        ----------
        event
            The event to fire
        """

        for callback_fn in self._event_listeners_by_type.get(
            event.event_id, OrderedSet([])
        ):
            callback_fn(event)


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
