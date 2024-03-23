# pylint: disable=C0302,C0103

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
    cast,
    overload,
)

import attrs
from sqlalchemy import Engine, ForeignKey, create_engine, delete, select
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    declared_attr,
    mapped_column,
    relationship,
)

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

    system_type: Type[Any]
    """The class type of the system."""
    message: str
    """An error message."""

    def __init__(self, system_type: Type[Any]) -> None:
        """
        Parameters
        ----------
        system_type
            The type of the resource not found.
        """
        super().__init__()
        self.system_type = system_type
        self.message = f"Could not find system with type: {system_type.__name__}."

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


class GameData(DeclarativeBase):
    """Base class required by SQLAlchemy."""


class Entity(GameData):
    """Collects all GameObject keys into a single table jor joining"""

    __tablename__ = "entity"

    uid: Mapped[int] = mapped_column(primary_key=True, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    name: Mapped[str] = mapped_column(default="")


class Component(AbstractConcreteBase, GameData):
    """Base class for all GameObject Components."""

    strict_attrs = True

    __allow_unmapped__ = True

    gameobject: GameObject

    @declared_attr
    @classmethod
    def uid(cls) -> Mapped[int]:
        """Create mapped uid attribute for components."""
        return mapped_column(ForeignKey("entity.uid"), primary_key=True, unique=True)

    @declared_attr
    @classmethod
    def entity(cls) -> Mapped[Entity]:
        """Create mapped entity attribute for components."""
        return relationship("Entity")


class GameObject:
    """A reference to an entity within the world.

    GameObjects wrap a unique integer identifier and provide an interface to access
    associated components and child/parent gameobjects.
    """

    __slots__ = ("world", "entity", "components", "children", "parent", "metadata")

    _next_game_object_uid: ClassVar[int] = 1

    world: World
    """Reference to the world the GameObject belongs to."""
    entity: Entity
    """Reference to the GameObject's entity table entry."""
    components: dict[Type[Component], Component]
    """Components attached to this GameObject."""
    children: list[GameObject]
    """Child GameObjects below this one in the hierarchy."""
    parent: Optional[GameObject]
    """The parent GameObject that this GameObject is a child of."""
    metadata: dict[str, Any]
    """Metadata associated with this GameObject."""

    def __init__(self, world: World, entity: Entity) -> None:
        self.world = world
        self.entity = entity
        self.components = {}
        self.parent = None
        self.children = []
        self.metadata = {}

    @property
    def uid(self) -> int:
        """A GameObject's ID."""
        return self.entity.uid

    @property
    def exists(self) -> bool:
        """Check if the GameObject still exists in the ECS.

        Returns
        -------
        bool
            True if the GameObject exists, False otherwise.
        """
        return self.uid in self.world.gameobjects

    @property
    def is_active(self) -> bool:
        """Check if a GameObject is active."""
        return self.has_component(Active)

    @property
    def name(self) -> str:
        """Get the GameObject's name"""
        return self.entity.name

    @name.setter
    def name(self, value: str) -> None:
        """Set the GameObject's name"""
        self.entity.name = value
        self.world.session.flush()

    def activate(self) -> None:
        """Tag the GameObject as active."""
        self.add_component(Active)

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
            return tuple(self.components.values())
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
        return tuple(self.components.keys())

    def add_component(self, component_type: Type[_CT], **kwargs: Any) -> _CT:
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
        component = component_type(**{**kwargs, "uid": self.uid})
        component.gameobject = self
        self.world.session.add(component)
        self.world.session.flush()
        self.components[component_type] = component

        return component

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
        if component_type in self.components:

            self.get_component(component_type)
            del self.components[component_type]
            self.world.session.execute(
                delete(component_type).where(component_type.uid == self.uid)
            )

            return True

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
        if component_type in self.components:
            return cast(component_type, self.components[component_type])

        raise ComponentNotFoundError(component_type)

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
        return all(ct in self.components for ct in component_types)

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
        return component_type in self.components

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
        return cast(component_type, self.components.get(component_type))

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

        # Deactivate first
        self.deactivate()

        # Destroy all children
        for child in self.children:
            child.destroy()

        # Destroy attached components
        for component_type in self.components:
            self.remove_component(component_type)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GameObject):
            return self.uid == other.uid
        return False

    def __int__(self) -> int:
        return self.uid

    def __hash__(self) -> int:
        return self.uid

    def __str__(self) -> str:
        component_types = [ct.__name__ for ct in self.components]
        return f"GameObject(uid={self.uid!r}, components={component_types!r}"

    def __repr__(self) -> str:
        component_types = [ct.__name__ for ct in self.components]
        return f"GameObject(uid={self.uid!r}, components={component_types!r}"

    @classmethod
    def create_new(
        cls,
        world: World,
        components: Optional[dict[Type[Component], dict[str, Any]]] = None,
        name: str = "",
    ) -> GameObject:
        """Create a new gameobject and return its UID."""

        uid: int = cls._next_game_object_uid
        cls._next_game_object_uid += 1

        obj = cls(world, Entity(uid=uid, name=name))

        if components:
            for component_type, component_args in components.items():
                component = component_type(**{**component_args, "uid": uid})
                component.gameobject = obj
                world.session.add(component)
                obj.components[component_type] = component

        world.session.flush()

        return obj


class Active(Component):
    """Tags a GameObject as active within the simulation."""

    __tablename__ = "active"


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

        raise SystemNotFoundError(system_type)

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

    _event_listeners_by_type: defaultdict[str, list[Callable[[Event], None]]]
    """Event listeners that are only called when a specific type of event fires."""

    def __init__(self) -> None:
        self._event_listeners_by_type = defaultdict(list)

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
        self._event_listeners_by_type[event_name].append(listener)

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

        for callback_fn in self._event_listeners_by_type.get(event.event_id, []):
            callback_fn(event)


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
        "rng",
        "resources",
        "gameobjects",
        "systems",
        "events",
        "db_engine",
        "session",
    )

    rng: random.Random
    """Random number generator."""
    component_types: dict[str, Type[Component]]
    """Components registered with the ECS."""
    gameobjects: dict[int, GameObject]
    """Mapping of GameObjects to unique identifiers."""
    resources: ResourceManager
    """Global resources shared by systems in the ECS."""
    systems: SystemManager
    """The systems run every simulation step."""
    events: EventManager
    """Manages event listeners."""
    db_engine: Engine
    """A reference to the database engine."""
    session: Session
    """A reference to the database session."""

    def __init__(self, rng_seed: Optional[Union[str, int]] = None) -> None:
        self.rng = random.Random(rng_seed)
        self.resources = ResourceManager()
        self.systems = SystemManager(self)
        self.events = EventManager()
        self.gameobjects = {}
        self.db_engine = create_engine("sqlite+pysqlite:///:memory:", echo=False)
        self.session = Session(self.db_engine)
        GameData.registry.configure()
        GameData.metadata.create_all(self.db_engine)

    def register_component_type(self, component_type: Type[Component]) -> None:
        """Register a component type with the ECS."""
        self.component_types[component_type.__name__] = component_type

    @overload
    def get_components(self, component_types: tuple[Type[_T1]]) -> list[tuple[_T1]]: ...

    @overload
    def get_components(
        self, component_types: tuple[Type[_T1], Type[_T2]]
    ) -> list[tuple[_T1, _T2]]: ...

    @overload
    def get_components(
        self, component_types: tuple[Type[_T1], Type[_T2], Type[_T3]]
    ) -> list[tuple[_T1, _T2, _T3]]: ...

    @overload
    def get_components(
        self, component_types: tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4]]
    ) -> list[tuple[_T1, _T2, _T3, _T4]]: ...

    @overload
    def get_components(
        self,
        component_types: tuple[Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5]],
    ) -> list[tuple[_T1, _T2, _T3, _T4, _T5]]: ...

    @overload
    def get_components(
        self,
        component_types: tuple[
            Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6]
        ],
    ) -> list[tuple[_T1, _T2, _T3, _T4, _T5, _T6]]: ...

    @overload
    def get_components(
        self,
        component_types: tuple[
            Type[_T1], Type[_T2], Type[_T3], Type[_T4], Type[_T5], Type[_T6], Type[_T7]
        ],
    ) -> list[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]: ...

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
    ) -> list[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]: ...

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
        list[tuple[_T1]],
        list[tuple[_T1, _T2]],
        list[tuple[_T1, _T2, _T3]],
        list[tuple[_T1, _T2, _T3, _T4]],
        list[tuple[_T1, _T2, _T3, _T4, _T5]],
        list[tuple[_T1, _T2, _T3, _T4, _T5, _T6]],
        list[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]],
        list[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]],
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
        if len(component_types) == 0:
            return []

        reference_component = component_types[0]

        query = select(*component_types)

        for entry in component_types[1:]:
            query = query.join(entry, entry.uid == reference_component.uid)

        # We ignore the type below to save the headache of trying to cast.
        return self.session.execute(query).all()  # type: ignore

    def step(self) -> None:
        """Advance the simulation as single tick and call all the systems."""
        self.session.flush()
        self.systems.update_systems()
