"""
Custom Entity component implementation that blends
the Unity-style workflow with the logic from the
Python esper library.

Sources:
https://github.com/benmoran56/esper
"""
from abc import ABC, abstractmethod
from typing import Dict, Iterable, List, Optional, Set, Tuple, Type, TypeVar, cast, Any
from uuid import uuid1

from farmhash import FarmHash64

_CT = TypeVar("_CT", bound='Component')
_ST = TypeVar("_ST", bound='System')
_RT = TypeVar("_RT", bound='Any')


class GameObject:
    """The core class on which all entities are built

    Attributes
    ----------
    id: int
        GameObject's UUID
    name: string
        GameObject's name
    tags: List[string]
        Associated tag strings
    _components: Dict[Type, Components]
        Components attached to this GameObject
    """

    __slots__ = "_id", "_name", "_tags", "_components"

    def __init__(
            self,
            name: str = "GameObject",
            tags: Iterable[str] = (),
            components: Iterable['Component'] = None
    ) -> None:
        self._id: int = FarmHash64(str(uuid1()))
        self._name: str = name
        self._tags: Set[str] = set(tags)
        self._components: Dict[str, 'Component'] = {}
        if components:
            for component in components:
                self.add_component(component)

    @property
    def id(self) -> int:
        """Return GameObject's ID"""
        return self._id

    @property
    def name(self) -> str:
        """Returns GameObject's name"""
        return self._name

    @property
    def tags(self) -> Set[str]:
        """Return tags associated with this GameObject"""
        return self._tags

    def set_name(self, name: str) -> None:
        """Change the GameObject's name"""
        self._name = name

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

    def add_component(self, component: 'Component') -> None:
        """Add a component to this GameObject"""
        component.set_gameobject(self)
        component.on_add()
        self._components[type(component).__name__] = component

    def remove_component(self, component: 'Component') -> None:
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

    def start(self) -> None:
        for component in self._components.values():
            component.on_start()

    def on_destroy(self) -> None:
        """Callback for when this GameObject is destroyed"""
        for component in self._components.values():
            component.on_destroy()

    def __hash__(self) -> int:
        return self._id

    def __repr__(self) -> str:
        return "GameObject(id={}, name={}, tags={}, components={})".format(
            self.id,
            self.name,
            self.tags,
            tuple(self._components.keys())
        )


class Component(ABC):
    """Component attached to a game object"""

    __slots__ = "_gameobject"

    def __init__(self) -> None:
        super().__init__()
        self._gameobject: Optional[GameObject] = None

    @property
    def gameobject(self) -> 'GameObject':
        if self._gameobject is None:
            raise TypeError("Component's GameObject is None")
        return self._gameobject

    def set_gameobject(self, gameobject: Optional['GameObject']) -> None:
        """Set the gameobject instance for this component"""
        self._gameobject = gameobject

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


class System(ABC):
    """Abstract base class for ECS systems"""

    __slots__ = "_priority", "_world"

    def __init__(self) -> None:
        super().__init__()
        self._priority: int = 0
        self._world: Optional['World'] = None

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def world(self) -> 'World':
        if self._world is None:
            raise TypeError("System's World is None")
        return self._world

    def set_world(self, world: 'World') -> None:
        self._world = world

    def set_priority(self, priority: int) -> None:
        self._priority = priority

    @abstractmethod
    def process(self, *args, **kwargs) -> None:
        raise NotImplementedError()


class World:
    """Collection of GameObjects"""

    __slots__ = "_gameobjects", "_dead_gameobjects", "_systems", "_resources"

    def __init__(self) -> None:
        self._gameobjects: Dict[int, GameObject] = {}
        self._dead_gameobjects: List[int] = []
        self._systems: List[System] = []
        self._resources: Dict[str, Any] = {}

    def add_gameobject(self, gameobject: GameObject) -> None:
        """Add gameobject to the world"""
        self._gameobjects[gameobject.id] = gameobject
        gameobject.start()

    def get_gameobject(self, gid: int) -> GameObject:
        """Retrieve the GameObject with the given id"""
        return self._gameobjects[gid]

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

    def get_components(self, *component_types: Type[_CT]) -> List[Tuple[int, Tuple[_CT, ...]]]:
        """Get all game objects with the given components"""
        components: List[Tuple[int, Tuple[_CT, ...]]] = []
        for gid, gameobject in self._gameobjects.items():
            try:
                components.append(
                    (gid, tuple([gameobject.get_component(c) for c in component_types])))
            except KeyError:
                continue
        return components

    def _clear_dead_gameobjects(self) -> None:
        """Delete gameobjects that were removed from the world"""
        for gameobject_id in self._dead_gameobjects:
            self._gameobjects[gameobject_id].on_destroy()
            del self._gameobjects[gameobject_id]

        self._dead_gameobjects.clear()

    def add_system(self, system: System, priority=0) -> None:
        """Add a System instance to the World"""
        system.set_priority(priority)
        system.set_world(self)
        self._systems.append(system)
        self._systems.sort(key=lambda proc: proc.priority, reverse=True)

    def remove_system(self, system_type: Type[System]) -> None:
        """Remove a System from the World"""
        for system in self._systems:
            if type(system) == system_type:
                self._systems.remove(system)

    def get_system(self, system_type: Type[_ST]) -> Optional[_ST]:
        """Get a System instance"""
        for system in self._systems:
            if type(system) == system_type:
                return cast(_ST, system)
        else:
            return None

    def process(self, *args, **kwargs) -> None:
        """Call the process method on all systems"""
        self._clear_dead_gameobjects()
        for system in self._systems:
            system.process(*args, **kwargs)

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
