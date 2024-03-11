"""Neighborly ECS GameObject Implementation.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Optional, Type, TypeVar

import esper
from ordered_set import OrderedSet

from neighborly.ecs.component import Active, Component
from neighborly.ecs.errors import ComponentNotFoundError, GameObjectNotFoundError

if TYPE_CHECKING:
    from neighborly.ecs.world import World


_CT = TypeVar("_CT", bound="Component")


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
            raise ComponentNotFoundError(component_type.__name__) from exc

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

        raise ComponentNotFoundError(component_type.__name__)

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
