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

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Iterable, List, Optional, Tuple, Type, TypeVar

import esper  # type: ignore
from ordered_set import OrderedSet  # type: ignore

logger = logging.getLogger(__name__)


_CT = TypeVar("_CT", bound="Component")
_RT = TypeVar("_RT", bound="Any")
_ST = TypeVar("_ST", bound="ISystem")


class ResourceNotFoundError(Exception):
    def __init__(self, resource_type: Type[Any]) -> None:
        super().__init__()
        self.resource_type: Type[Any] = resource_type
        self.message = f"Could not find resource with type: {resource_type.__name__}"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.resource_type})"


class GameObjectNotFoundError(Exception):
    def __init__(self, gid: int) -> None:
        super().__init__()
        self.gid: int = gid
        self.message = f"Could not find GameObject with id: {gid}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.gid})"


class ComponentNotFoundError(Exception):
    def __init__(self, component_type: Type[Component]) -> None:
        super().__init__()
        self.component_type: Type[Component] = component_type
        self.message = f"Could not find Component with type: {component_type.__name__}."

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.component_type})"


class GameObject:
    """
    Collections of components that share are unique identifier
    and represent entities within the game world

    Attributes
    ----------
    _id: int
      unique identifier
    _name: str
        name of the GameObject
    _world: World
        the World instance this GameObject belongs to
    children: List[GameObject]
        Other GameObjects that are below this one in the hierarchy
        and are removed when the parent is removed
    parent: Optional[GameObject]
        The GameObject that this GameObject is a child of
    """

    __slots__ = "_id", "_name", "_world", "children", "parent"

    def __init__(
        self,
        unique_id: int,
        world: World,
        name: Optional[str] = None,
        components: Optional[Iterable[Component]] = None,
    ) -> None:
        self._name: str = name if name else f"GameObject ({unique_id})"
        self._id: int = unique_id
        self._world: World = world
        self.parent: Optional[GameObject] = None
        self.children: List[GameObject] = []

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
    def world(self) -> World:
        """Return the world that this GameObject belongs to"""
        return self._world

    @property
    def components(self) -> Tuple[Component, ...]:
        """Returns the component instances associated with this GameObject"""
        try:
            return self.world.ecs.components_for_entity(self.id)
        except KeyError:
            # Ignore errors if gameobject is not found in esper ecs
            return ()

    def get_component_types(self) -> Tuple[Type[Component], ...]:
        """Returns the types of components attached to this character"""
        return tuple(map(lambda component: type(component), self.components))

    def add_component(self, component: Component) -> GameObject:
        """Add a component to this GameObject"""
        component.set_gameobject(self)
        self.world.ecs.add_component(self.id, component)
        return self

    def remove_component(
        self, component_type: Type[Component], immediate: bool = True
    ) -> None:
        """Add a component to this GameObject"""
        try:
            command = RemoveComponentCommand(self, component_type)

            if immediate:
                command.run(self.world)
            else:
                self.world.command_queue.append(command)
        except KeyError:
            pass

    def get_component(self, component_type: Type[_CT]) -> _CT:
        try:
            return self.world.ecs.component_for_entity(self.id, component_type)  # type: ignore
        except KeyError:
            raise ComponentNotFoundError(component_type)

    def has_component(self, *component_type: Type[Component]) -> bool:
        try:
            return all(
                [self.world.ecs.try_component(self.id, ct) for ct in component_type]
            )
        except KeyError:
            return False

    def try_component(self, component_type: Type[_CT]) -> Optional[_CT]:
        try:
            return self.world.ecs.try_component(self.id, component_type)  # type: ignore
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
        """Get a single instance of a component type attached to a child"""
        for child in self.children:
            if component := child.try_component(component_type):
                return child.id, component
        raise ComponentNotFoundError(component_type)

    def get_component_in_children(
        self, component_type: Type[_CT]
    ) -> List[Tuple[int, _CT]]:
        """Get all the instances of a component type attached to the immediate children of this GameObject"""
        results: List[Tuple[int, _CT]] = []
        for child in self.children:
            if component := child.try_component(component_type):
                results.append((child.id, component))
        return results

    def destroy(self) -> None:
        self.world.delete_gameobject(self.id)

    def to_dict(self) -> Dict[str, Any]:
        ret = {
            "id": self.id,
            "name": self.name,
            "components": [c.to_dict() for c in self.components],
        }

        return ret

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GameObject):
            return self.id == other.id
        raise TypeError(f"Expected GameObject but was {type(object)}")

    def __hash__(self) -> int:
        return self._id

    def __str__(self) -> str:
        return f"GameObject(id={self.id})"

    def __repr__(self) -> str:
        return f"GameObject(id={self.id})"


class IEcsCommand:
    """A change that needs to be made to the ECS state"""

    @classmethod
    @abstractmethod
    def get_type(cls) -> str:
        raise NotImplementedError

    def run(self, world: World) -> None:
        raise NotImplementedError


class RemoveComponentCommand(IEcsCommand):
    __slots__ = "gameobject", "component_type"

    def __init__(self, gameobject: GameObject, component_type: Type[Component]) -> None:
        super(IEcsCommand, self).__init__()
        self.gameobject: GameObject = gameobject
        self.component_type: Type[Component] = component_type

    @classmethod
    def get_type(cls) -> str:
        return cls.__name__

    def run(self, world: World) -> None:
        if not self.gameobject.has_component(self.component_type):
            return
        world.ecs.remove_component(self.gameobject.id, self.component_type)


class Component(ABC):
    """
    Components are collections of related data attached to GameObjects.

    Attributes
    ----------
    _gameobject: Optional[GameObject]
        Reference to the gameobject this component is attached to
    """

    __slots__ = "_gameobject"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the component to a dict"""
        return {"type": self.__class__.__name__}

    def __repr__(self) -> str:
        return "{}".format(self.__class__.__name__)


class ISystem(ABC, esper.Processor):
    world: World

    def __init__(self):
        super(esper.Processor, self).__init__()


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
        "_command_queue",
    )

    def __init__(self) -> None:
        self._ecs: esper.World = esper.World()
        self._gameobjects: Dict[int, GameObject] = {}
        self._dead_gameobjects: OrderedSet[int] = OrderedSet()
        self._resources: Dict[Type[Any], Any] = {}
        self._command_queue: List[IEcsCommand] = []

    @property
    def ecs(self) -> esper.World:
        return self._ecs

    @property
    def command_queue(self) -> List[IEcsCommand]:
        return self._command_queue

    def spawn_gameobject(
        self, components: Optional[List[Component]] = None, name: Optional[str] = None
    ) -> GameObject:
        """Create a new gameobject and attach any given component instances"""
        entity_id = self._ecs.create_entity(*components if components else [])
        gameobject = GameObject(
            unique_id=entity_id,
            components=components,
            world=self,
            name=(name if name else f"GameObject({entity_id})"),
        )
        self._gameobjects[gameobject.id] = gameobject
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

    def try_gameobject(self, gid: int) -> Optional[GameObject]:
        """Retrieve the GameObject with the given id"""
        return self._gameobjects.get(gid)

    def delete_gameobject(self, gid: int) -> None:
        """Remove gameobject from world"""
        self._dead_gameobjects.append(gid)

        # Recursively remove all children
        for child in self._gameobjects[gid].children:
            self.delete_gameobject(child.id)

    def get_component(self, component_type: Type[_CT]) -> List[Tuple[int, _CT]]:
        """Get all the gameobjects that have a given component type"""
        return self._ecs.get_component(component_type)  # type: ignore

    def get_components(
        self, *component_types: Type[_CT]
    ) -> List[Tuple[int, List[_CT]]]:
        """Get all game objects with the given components"""
        return self._ecs.get_components(*component_types)  # type: ignore

    def _clear_dead_gameobjects(self) -> None:
        """Delete gameobjects that were removed from the world"""
        for gameobject_id in self._dead_gameobjects:
            if len(self._gameobjects[gameobject_id].components) > 0:
                self._ecs.delete_entity(gameobject_id, True)

            gameobject = self._gameobjects[gameobject_id]

            if gameobject.parent is not None:
                gameobject.parent.remove_child(gameobject)

            del self._gameobjects[gameobject_id]
        self._dead_gameobjects.clear()

    def clear_command_queue(self) -> None:
        while self._command_queue:
            command = self._command_queue.pop(0)
            command.run(self)

    def add_system(self, system: ISystem, priority: int = 0) -> None:
        """Add a System instance to the World"""
        self._ecs.add_processor(system, priority=priority)
        system.world = self

    def get_system(self, system_type: Type[_ST]) -> Optional[_ST]:
        """Get a System of the given type"""
        return self._ecs.get_processor(system_type)

    def remove_system(self, system_type: Type[ISystem]) -> None:
        """Remove a System from the World"""
        self._ecs.remove_processor(system_type)

    def step(self, **kwargs: Any) -> None:
        """Call the process method on all systems"""
        self._clear_dead_gameobjects()
        self._ecs.process(**kwargs)  # type: ignore
        self.clear_command_queue()

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

    def __repr__(self) -> str:
        return "World(gameobjects={}, resources={})".format(
            len(self._gameobjects),
            list(self._resources.values()),
        )


class IComponentFactory(ABC, Generic[_CT]):
    """Abstract base class for creating Component instances"""

    @abstractmethod
    def create(self, world: World, **kwargs: Any) -> _CT:
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
        _CT
            Component instance
        """
        raise NotImplementedError
