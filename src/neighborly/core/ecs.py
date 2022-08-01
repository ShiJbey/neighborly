"""
Custom Entity-Component implementation that blends
the Unity-style GameObjects with the ECS logic from the
Python esper library and the Bevy Game Engine.

Sources:
https://docs.unity3d.com/ScriptReference/GameObject.html
https://github.com/benmoran56/esper
https://github.com/bevyengine/bevy
"""
from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    cast,
)
from uuid import uuid1

logger = logging.getLogger(__name__)

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")


class Event(Protocol):
    """
    Events are things that happen in the story world that GameObjects can react to.
    """

    def get_type(self) -> str:
        """Return the type of this event"""
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        raise NotImplemented


class IEventListener(ABC):
    """Abstract interface that components inherit from when they want to listen for events"""

    @abstractmethod
    def will_handle_event(self, event: Event) -> bool:
        """
        Check the preconditions for this event type to see if they pass

        Returns
        -------
        bool
            True if the event passes all the preconditions
        """
        raise NotImplementedError()

    @abstractmethod
    def handle_event(self, event: Event) -> bool:
        """
        Perform logic when an event occurs

        Returns
        -------
        bool
            True if the event was handled successfully
        """
        raise NotImplementedError()


class GameObject:
    """
    Collections of components that share are unique identifier
    and represent entities within the game world

    Attributes
    ----------
    id: int
        unique identifier
    name: str
        name of the GameObject
    world: World
        the World instance this GameObject belongs to
    components: List[Components]
        Components attached to this GameObject
    """

    __slots__ = (
        "_id",
        "_name",
        "_components",
        "_world",
        "_archetype",
        "_event_listeners",
    )

    def __init__(
        self,
        name: str = "GameObject",
        components: Iterable[Component] = (),
        world: Optional[World] = None,
        archetype: Optional[EntityArchetype] = None,
    ) -> None:
        self._name: str = name
        self._id: int = self.generate_id()
        self._world: Optional[World] = world
        self._components: Dict[str, Component] = {}
        self._archetype: Optional[EntityArchetype] = archetype
        self._event_listeners: List[IEventListener] = []

        if components:
            for component in components:
                self.add_component(component)

    @property
    def id(self) -> int:
        """Return GameObject's ID"""
        return self._id

    @property
    def name(self) -> str:
        """Get the name of the GameObject"""
        return self._name

    @property
    def archetype(self) -> Optional[EntityArchetype]:
        """Return the name of the archetype for creating this GameObject"""
        return self._archetype

    @property
    def world(self) -> World:
        """Return the world that this GameObject belongs to"""
        if self._world:
            return self._world
        raise TypeError("World is None for GameObject")

    @property
    def components(self) -> List[Component]:
        return list(self._components.values())

    def set_world(self, world: Optional[World]) -> None:
        """set the world instance"""
        self._world = world

    def add_component(self, component: Component) -> GameObject:
        """Add a component to this GameObject"""
        component.set_gameobject(self)
        self._components[type(component).__name__] = component
        if isinstance(component, IEventListener):
            self._event_listeners.append(component)
        component.on_add()
        return self

    def remove_component(self, component_type: Type[_CT]) -> None:
        """Add a component to this GameObject"""
        component = self._components[component_type.__name__]
        if isinstance(component, IEventListener):
            self._event_listeners.remove(component)
        component.on_remove()
        del self._components[component_type.__name__]

    def get_component(self, component_type: Type[_CT]) -> _CT:
        return cast(_CT, self._components[component_type.__name__])

    def has_component(self, component_type: Type[_CT]) -> bool:
        return component_type.__name__ in self._components

    def try_component(self, component_type: Type[_CT]) -> Optional[_CT]:
        return cast(Optional[_CT], self._components.get(component_type.__name__))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "components": [c.to_dict() for c in self._components.values()],
            "archetype": self.archetype.name if self.archetype else "",
        }

    def handle_event(self, event: Event) -> None:
        """Handle an event acting on this gameobject"""
        for listener in self._event_listeners:
            listener.handle_event(event)

    def will_handle_event(self, event: Event) -> bool:
        """Return False if this gameobject rejects this event, True otherwise"""
        if self._event_listeners:
            return all(
                [
                    listener.will_handle_event(event)
                    for listener in self._event_listeners
                ]
            )
        return True

    def __hash__(self) -> int:
        return self._id

    @staticmethod
    def generate_id() -> int:
        """Create a new unique int ID"""
        return int.from_bytes(hashlib.sha256(uuid1().bytes).digest()[:8], "little")


class Component(ABC):
    """
    Components are collections of related data attached to GameObjects.

    Attributes
    ----------
    _gameobject: Optional[GameObject]
        Reference to the gameobject this component is attached to
    """

    __slots__ = "_gameobject"

    def __init__(self) -> None:
        super().__init__()
        self._gameobject: Optional[GameObject] = None

    @property
    def gameobject(self) -> GameObject:
        """Returns the GameObject this component is attached to"""
        if self._gameobject is None:
            raise TypeError("Component's GameObject is None")
        return self._gameobject

    def set_gameobject(self, gameobject: Optional[GameObject]) -> None:
        """set the gameobject instance for this component"""
        self._gameobject = gameobject

    def on_add(self) -> None:
        """Run when the component is added to the GameObject"""
        return

    def on_remove(self) -> None:
        """Run when the component is removed from the GameObject"""
        return

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        """Create an instance of the component using a reference to the World object and additional parameters"""
        raise cls()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the component to a dict"""
        return {"type": self.__class__.__name__}


class ISystem(Protocol):
    """
    Abstract base class for ECS systems.
    Systems perform processes on components and are where the main simulation logic lives.
    """

    @abstractmethod
    def __call__(self, world: World, **kwargs) -> None:
        raise NotImplementedError()


class World:
    """Collection of GameObjects"""

    __slots__ = (
        "_gameobjects",
        "_dead_gameobjects",
        "_systems",
        "_resources",
        "_setup_systems",
        "_world_setup",
    )

    def __init__(self) -> None:
        self._gameobjects: Dict[int, GameObject] = {}
        self._dead_gameobjects: List[int] = []
        self._systems: List[Tuple[int, ISystem]] = []
        self._setup_systems: List[Tuple[int, ISystem]] = []
        self._resources: Dict[str, Any] = {}
        self._world_setup: bool = False

    def add_gameobject(self, gameobject: GameObject) -> None:
        """Add gameobject to the world"""
        self._gameobjects[gameobject.id] = gameobject
        gameobject.set_world(self)

    def get_gameobject(self, gid: int) -> GameObject:
        """Retrieve the GameObject with the given id"""
        return self._gameobjects[gid]

    def get_gameobjects(self) -> List[GameObject]:
        """Get all gameobjects"""
        return list(self._gameobjects.values())

    def has_gameobject(self, gid: int) -> bool:
        """Check that a GameObject with the given id exists"""
        return gid in self._gameobjects

    def try_gameobject(self, gid: int) -> Optional[GameObject]:
        """Retrieve the GameObject with the given id"""
        return self._gameobjects.get(gid)

    def delete_gameobject(self, gid: int) -> None:
        """Remove gameobject from world"""
        self._dead_gameobjects.append(gid)

    def get_component(self, component_type: Type[_CT]) -> List[Tuple[int, _CT]]:
        """Get all the gameobjects that have a given component type"""
        components: List[Tuple[int, _CT]] = []
        for gid, gameobject in self._gameobjects.items():
            component = gameobject.try_component(component_type)
            if component is not None:
                components.append((gid, component))
        return components

    def get_components(
        self, *component_types: Type[_CT]
    ) -> List[Tuple[int, Tuple[_CT, ...]]]:
        """Get all game objects with the given components"""
        components: List[Tuple[int, Tuple[_CT, ...]]] = []
        for gid, gameobject in self._gameobjects.items():
            try:
                components.append(
                    (gid, tuple([gameobject.get_component(c) for c in component_types]))
                )
            except KeyError:
                continue
        return components

    def _clear_dead_gameobjects(self) -> None:
        """Delete gameobjects that were removed from the world"""
        for gameobject_id in self._dead_gameobjects:
            gameobject = self._gameobjects[gameobject_id]
            if gameobject.archetype:
                gameobject.archetype.decrement_instances()
            gameobject.set_world(None)
            del self._gameobjects[gameobject_id]

        self._dead_gameobjects.clear()

    def add_system(self, system: ISystem, priority=0) -> None:
        """Add a System instance to the World"""
        self._systems.append((priority, system))
        self._systems.sort(key=lambda pair: pair[0], reverse=True)

    def remove_system(self, system: ISystem) -> None:
        """Remove a System from the World"""
        for entry in self._systems:
            _, s = entry
            if s == system:
                self._systems.remove(entry)

    def add_setup_system(self, system: ISystem, priority=0) -> None:
        """Add a setup System instance to the World"""
        self._setup_systems.append((priority, system))
        self._setup_systems.sort(key=lambda pair: pair[0], reverse=True)

    def step(self, **kwargs) -> None:
        """Call the process method on all systems"""
        self._clear_dead_gameobjects()

        if self._world_setup is False:
            for _, system in self._setup_systems:
                system(self, **kwargs)
            self._world_setup = True

        for _, system in self._systems:
            system(self, **kwargs)

    def add_resource(self, resource: Any) -> None:
        """Add a global resource to the world"""
        resource_type = type(resource)
        if resource_type in self._resources:
            logger.warning(f"Replacing existing resource of type: {resource_type}")
        self._resources[resource_type] = resource

    def remove_resource(self, resource_type: Any) -> None:
        """remove a global resource to the world"""
        del self._resources[resource_type]

    def get_resource(self, resource_type: Type[_RT]) -> _RT:
        """Add a global resource to the world"""
        return self._resources[resource_type]

    def has_resource(self, resource_type: Any) -> bool:
        """Return true if the world has the given resource"""
        return resource_type in self._resources

    def try_resource(self, resource_type: Type[_RT]) -> Optional[_RT]:
        """Return the resource if it exists, None otherwise"""
        return self._resources.get(resource_type)

    def __repr__(self) -> str:
        return "World(gameobjects={}, resources={}, systems={})".format(
            {g.id: g for g in self._gameobjects.values()},
            list(self._resources.values()),
            [s[1] for s in self._systems],
        )


class EntityArchetype:
    """
    Organizes information for constructing components that compose GameObjects.

    Attributes
    ----------
    _name: str
        (Read-only) The name of the entity archetype
    _components: Dict[Type[Component], Dict[str, Any]]
        Dict of components used to construct this archetype
    """

    __slots__ = "_name", "_components", "_instances"

    def __init__(self, name: str) -> None:
        self._name: str = name
        self._components: Dict[Type[Component], Dict[str, Any]] = {}
        self._instances: int = 0

    @property
    def name(self) -> str:
        """Returns the name of this archetype"""
        return self._name

    @property
    def components(self) -> Dict[Type[Component], Dict[str, Any]]:
        """Returns a list of components in this archetype"""
        return {**self._components}

    @property
    def instances(self) -> int:
        return self._instances

    def add(self, component_type: Type[Component], **kwargs: Any) -> EntityArchetype:
        """
        Add a component to this archetype

        Parameters
        ----------
        component_type: subclass of neighborly.core.ecs.Component
            The component type to add to the entity archetype
        **kwargs: Dict[str, Any]
            Attribute overrides to pass to the component
        """
        self._components[component_type] = {**kwargs}
        return self

    def increment_instances(self) -> None:
        self._instances += 1

    def decrement_instances(self) -> None:
        self._instances -= 1

    def spawn(self, world: World) -> GameObject:
        """Create a new GameObject from the Archetype and add it to the world"""
        gameobject = GameObject(name=self.name, archetype=self)

        for component_type, options in self.components.items():
            gameobject.add_component(component_type.create(world, **options))

        world.add_gameobject(gameobject)

        self.increment_instances()

        return gameobject

    def __repr__(self) -> str:
        return "{}(name={}, components={})".format(
            self.__class__.__name__, self._name, self._components
        )
