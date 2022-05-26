"""
Custom Entity component implementation that blends
the Unity-style workflow with the logic from the
Python esper library.

Sources:
https://github.com/benmoran56/esper
"""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from typing import (
    Any,
    Iterable,
    Optional,
    Protocol,
    Type,
    TypeVar,
    cast,
)
from uuid import uuid1

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")


class GameObject:
    """The core class on which all entities are built

    Attributes
    ----------
    id: int
        unique identifier
    tags: list[string]
        Associated tag strings
    world: World
        the World instance this GameObject belongs to
    _components: dict[Type, Components]
        Components attached to this GameObject
    """

    __slots__ = "_id", "_tags", "_components", "_world", "_active", "_archetype_name"

    def __init__(
        self,
        tags: Iterable[str] = (),
        components: Iterable[Component] = (),
        world: Optional[World] = None,
        archetype_name: Optional[str] = None,
    ) -> None:
        self._id: int = self.generate_id()
        self._active: bool = True
        self._tags: set[str] = set(tags)
        self._world: Optional[World] = world
        self._components: dict[str, Component] = {}
        self._archetype_name: Optional[str] = archetype_name

        if components:
            for component in components:
                self.add_component(component)

    @property
    def id(self) -> int:
        """Return GameObject's ID"""
        return self._id

    @property
    def tags(self) -> set[str]:
        """Return tags associated with this GameObject"""
        return self._tags

    @property
    def archetype_name(self) -> Optional[str]:
        return self._archetype_name

    @property
    def world(self) -> World:
        """Return the world that this GameObject belongs to"""
        if self._world:
            return self._world
        raise TypeError("World is None for GameObject")

    @property
    def active(self) -> bool:
        return self._active

    def set_world(self, world: Optional[World]) -> None:
        """set the world instance"""
        self._world = world

    def set_active(self, is_active: bool) -> None:
        self._active = is_active

    def add_tags(self, *tags: str) -> None:
        """Add tags to this GameObject"""
        for tag in tags:
            self._tags.add(tag)

    def remove_tags(self, *tags: str) -> None:
        """Remove tags to this GameObject"""
        for tag in tags:
            self._tags.remove(tag)

    def has_tags(self, *tags: str) -> bool:
        """Add tags to this GameObject"""
        for tag in tags:
            if tag not in self._tags:
                return False
        return True

    def add_component(self, component: Component) -> None:
        """Add a component to this GameObject"""
        component.set_gameobject(self)
        component.on_add()
        self._components[type(component).__name__] = component

    def remove_component(self, component: Component) -> None:
        """Add a component to this GameObject"""
        component.on_remove()
        component.set_gameobject(None)
        del self._components[type(component).__name__]

    def get_component(self, component_type: Type[_CT]) -> _CT:
        return cast(_CT, self._components[component_type.__name__])

    def has_component(self, component_type: Type[_CT]) -> bool:
        return component_type.__name__ in self._components

    def try_component(self, component_type: Type[_CT]) -> Optional[_CT]:
        return cast(Optional[_CT], self._components.get(component_type.__name__))

    def get_component_with_name(self, name: str) -> Component:
        return self._components[name]

    def has_component_with_name(self, name: str) -> bool:
        return name in self._components

    def try_component_with_name(self, name: str) -> Optional[Component]:
        return self._components.get(name)

    def get_components(self) -> list[Component]:
        return list(self._components.values())

    def start(self) -> None:
        for component in self._components.values():
            component.on_start()

    def destroy(self) -> None:
        """Callback for when this GameObject is destroyed"""
        for component in self._components.values():
            component.on_destroy()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self._id,
            "tags": sorted([*self._tags]),
            "components": [c.to_dict() for c in self._components.values()],
        }

    def __hash__(self) -> int:
        return self._id

    def __repr__(self) -> str:
        return "GameObject(id={}, tags={}, components={})".format(
            self.id, self.tags, tuple(self._components.keys())
        )

    @staticmethod
    def generate_id() -> int:
        """Create a new unique int ID"""
        return int.from_bytes(hashlib.sha256(uuid1().bytes).digest()[:8], "little")


class Component(ABC):
    """Component attached to a game object"""

    __slots__ = "_gameobject"

    def __init__(self) -> None:
        super().__init__()
        self._gameobject: Optional[GameObject] = None

    @property
    def gameobject(self) -> GameObject:
        if self._gameobject is None:
            raise TypeError("Component's GameObject is None")
        return self._gameobject

    def set_gameobject(self, gameobject: Optional[GameObject]) -> None:
        """set the gameobject instance for this component"""
        self._gameobject = gameobject

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.__class__.__name__}

    def on_add(self) -> None:
        """Callback for when the component is added to a GameObject"""
        pass

    def on_remove(self) -> None:
        """Callback for when the component is removed to a GameObject"""
        pass

    def on_destroy(self) -> None:
        """Callback for when the GameObject's on_destroy method is called"""
        pass

    def on_start(self) -> None:
        """Callback for when the GameObject's start method is called"""
        pass


class ISystem(Protocol):
    """Abstract base class for ECS systems"""

    @abstractmethod
    def __call__(self, world: World, **kwargs) -> None:
        raise NotImplementedError()


class World:
    """Collection of GameObjects"""

    __slots__ = "_gameobjects", "_dead_gameobjects", "_systems", "_resources"

    def __init__(self) -> None:
        self._gameobjects: dict[int, GameObject] = {}
        self._dead_gameobjects: list[int] = []
        self._systems: list[tuple[int, ISystem]] = []
        self._resources: dict[str, Any] = {}

    def add_gameobject(self, gameobject: GameObject) -> None:
        """Add gameobject to the world"""
        self._gameobjects[gameobject.id] = gameobject
        gameobject.set_world(self)
        gameobject.start()

    def get_gameobject(self, gid: int) -> GameObject:
        """Retrieve the GameObject with the given id"""
        return self._gameobjects[gid]

    def get_gameobjects(self) -> list[GameObject]:
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

    def get_component(self, component_type: Type[_CT]) -> list[tuple[int, _CT]]:
        """Get all the gameobjects that have a given component type"""
        components: list[tuple[int, _CT]] = []
        for gid, gameobject in self._gameobjects.items():
            component = gameobject.try_component(component_type)
            if component is not None:
                components.append((gid, component))
        return components

    def get_component_by_name(self, name: str) -> list[tuple[int, Component]]:
        components: list[tuple[int, Component]] = []
        for gid, gameobject in self._gameobjects.items():
            component = gameobject.try_component_with_name(name)
            if component is not None:
                components.append((gid, component))
        return components

    def get_components(
        self, *component_types: Type[_CT]
    ) -> list[tuple[int, tuple[_CT, ...]]]:
        """Get all game objects with the given components"""
        components: list[tuple[int, tuple[_CT, ...]]] = []
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
            self._gameobjects[gameobject_id].destroy()
            self._gameobjects[gameobject_id].set_world(None)
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

    def process(self, **kwargs) -> None:
        """Call the process method on all systems"""
        self._clear_dead_gameobjects()
        for _, system in self._systems:
            system(self, **kwargs)

    def add_resource(self, resource: Any) -> None:
        """Add a global resource to the world"""
        self._resources[type(resource).__name__] = resource

    def remove_resource(self, resource: Type[_RT]) -> None:
        """remove a global resource to the world"""
        del self._resources[resource.__name__]

    def get_resource(self, resource: Type[_RT]) -> _RT:
        """Add a global resource to the world"""
        return self._resources[resource.__name__]

    def has_resource(self, resource: Type[_RT]) -> bool:
        """Return true if the world has the given resource"""
        return resource.__name__ in self._resources

    def try_resource(self, resource: Type[_RT]) -> Optional[_RT]:
        """Return the resource if it exists, None otherwise"""
        return self._resources.get(resource.__name__)
