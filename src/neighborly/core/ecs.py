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
from abc import ABC
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, TypeVar
from uuid import uuid1

import esper

logger = logging.getLogger(__name__)

_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")


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
    )

    def __init__(
        self,
        unique_id: Optional[int] = None,
        name: str = "GameObject",
        components: Iterable[Component] = (),
        world: Optional[World] = None,
        archetype: Optional[EntityArchetype] = None,
    ) -> None:
        self._name: str = name
        self._id: int = unique_id if unique_id else self.generate_id()
        self._world: Optional[World] = world
        self._components: Dict[Type[_CT], Component] = {}
        self._archetype: Optional[EntityArchetype] = archetype

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
        self._components[type(component)] = component
        self.world.ecs.add_component(self.id, component)
        component.on_add()
        return self

    def remove_component(self, component_type: Type[_CT]) -> None:
        """Add a component to this GameObject"""
        component = self._components[component_type]
        component.on_remove()
        self.world.ecs.remove_component(self.id, component_type)
        del self._components[component_type]

    def get_component(self, component_type: Type[_CT]) -> _CT:
        return self._components[component_type]

    def has_component(self, *component_type: Type[_CT]) -> bool:
        return all([ct in self._components for ct in component_type])

    def try_component(self, component_type: Type[_CT]) -> Optional[_CT]:
        return self._components.get(component_type)

    def archive(self) -> None:
        """
        Deactivates the GameObject by removing excess components.

        The GameObject stays in the ECS though.
        """
        for component in self.components:
            component.on_archive()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "components": [c.to_dict() for c in self._components.values()],
            "archetype": self.archetype.name if self.archetype else "",
        }

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

    def __init__(self, *args, **kwargs) -> None:
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

    def on_archive(self) -> None:
        """Run when the GameObject this is connected to is archived"""
        return

    @classmethod
    def create(cls, world: World, **kwargs) -> Component:
        """Create an instance of the component using a reference to the World object and additional parameters"""
        return cls(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the component to a dict"""
        return {"type": self.__class__.__name__}


class ISystem(ABC, esper.Processor):
    world: World

    def __init__(self):
        super().__init__()


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
    )

    def __init__(self) -> None:
        self._ecs: esper.World = esper.World()
        self._gameobjects: Dict[int, GameObject] = {}
        self._dead_gameobjects: List[int] = []
        self._resources: Dict[str, Any] = {}

    @property
    def ecs(self) -> esper.World:
        return self._ecs

    def spawn_gameobject(
        self, *components: Component, name: Optional[str] = None
    ) -> GameObject:
        """Create a new gameobject and attach any given component instances"""
        entity_id = self._ecs.create_entity(*components)
        gameobject = GameObject(
            unique_id=entity_id,
            components=components,
            world=self,
            name=(name if name else f"GameObject({entity_id})"),
        )
        self._gameobjects[gameobject.id] = gameobject
        return gameobject

    def spawn_archetype(self, archetype: EntityArchetype) -> GameObject:
        component_instances: List[Component] = []
        for component_type, options in archetype.components.items():
            component_instances.append(component_type.create(self, **options))

        entity_id = self._ecs.create_entity(*component_instances)
        gameobject = GameObject(
            unique_id=entity_id,
            components=component_instances,
            world=self,
            name=f"{archetype.name}({entity_id})",
            archetype=archetype,
        )

        archetype.increment_instances()

        self._gameobjects[gameobject.id] = gameobject

        return gameobject

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
        self._ecs.delete_entity(gid)
        self._dead_gameobjects.append(gid)

    def get_component(self, component_type: Type[_CT]) -> List[Tuple[int, _CT]]:
        """Get all the gameobjects that have a given component type"""
        return self._ecs.get_component(component_type)

    def get_components(
        self, *component_types: Type[_CT]
    ) -> List[Tuple[int, List[_CT, ...]]]:
        """Get all game objects with the given components"""
        return self._ecs.get_components(*component_types)

    def try_components(
        self, entity: int, *component_types: Type[_CT]
    ) -> Optional[List[List[_CT]]]:
        """Try to get a multiple component types for a GameObject."""
        return self._ecs.try_components(entity, *component_types)

    def _clear_dead_gameobjects(self) -> None:
        """Delete gameobjects that were removed from the world"""
        for gameobject_id in self._dead_gameobjects:
            gameobject = self._gameobjects[gameobject_id]
            for component in gameobject.components:
                component.on_remove()
            if gameobject.archetype:
                gameobject.archetype.decrement_instances()
            gameobject.set_world(None)
            del self._gameobjects[gameobject_id]

        self._dead_gameobjects.clear()

    def add_system(self, system: ISystem, priority: int = 0) -> None:
        """Add a System instance to the World"""
        self._ecs.add_processor(system, priority=priority)
        system.world = self

    def remove_system(self, system: Type[ISystem]) -> None:
        """Remove a System from the World"""
        self._ecs.remove_processor(system)
        system.world = None

    def step(self, **kwargs) -> None:
        """Call the process method on all systems"""
        self._clear_dead_gameobjects()
        self._ecs.process(**kwargs)

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

    def __repr__(self) -> str:
        return "World(gameobjects={}, resources={})".format(
            len(self._gameobjects),
            list(self._resources.values()),
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

    def __repr__(self) -> str:
        return "{}(name={}, components={})".format(
            self.__class__.__name__, self._name, self._components
        )
