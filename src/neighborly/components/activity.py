from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, Optional

from ordered_set import OrderedSet

from neighborly.core.ecs import (
    Component,
    EntityPrefab,
    GameObject,
    GameObjectFactory,
    ISerializable,
    TagComponent,
    World,
)


class ActivityType(TagComponent):
    """Tags a GameObject as being a type of activity."""

    pass


class Activities(Component, ISerializable):
    """A collection of activity names.

    Notes
    -----
    Activity names are case-insensitive and are all converted to lowercase upon storage.

    Systems may look for an Activities component to:

    1. Describe the activities available at a location
    2. Help characters determine where they frequent/want to go
    3. Add content to flesh out the narrative setting of the simulation
    """

    __slots__ = "_activities"

    _activities: OrderedSet[GameObject]
    """Activity names."""

    def __init__(self, activities: Optional[Iterable[GameObject]] = None) -> None:
        """
        Parameters
        ----------
        activities
            A collection of activities.
        """
        super().__init__()
        self._activities = OrderedSet(activities if activities else [])

    def to_dict(self) -> Dict[str, Any]:
        return {"activities": [a.name for a in self._activities]}

    def __iter__(self) -> Iterator[GameObject]:
        return self._activities.__iter__()

    def __contains__(self, activity: GameObject) -> bool:
        return activity in self._activities

    def __str__(self) -> str:
        return ", ".join([a.name for a in self._activities])

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({[a.name for a in self._activities]})"


class ActivityLibrary:
    """A collection of references to activity type GameObject instances."""

    __slots__ = "_activity_types", "_activities_to_instantiate"

    _activities_to_instantiate: OrderedSet[str]
    """The names of activity prefabs to instantiate at the start of the simulation."""

    _activity_types: Dict[str, GameObject]
    """Activity type names mapped to their GameObject instances."""

    def __init__(self) -> None:
        self._activities_to_instantiate = OrderedSet([])
        self._activity_types = {}

    @property
    def activities_to_instantiate(self) -> OrderedSet[str]:
        return self._activities_to_instantiate

    def add(self, activity: GameObject) -> None:
        """Add an activity type to the library.

        Parameters
        ----------
        activity
            An activity type entity.
        """
        self._activity_types[activity.name] = activity

    def get(self, name: str) -> GameObject:
        """Retrieve an activity type entity.

        Parameters
        ----------
        name
            The name of an activity type.

        Returns
        -------
        GameObject
            An activity type entity.
        """
        return self._activity_types[name]


def register_activity_type(world: World, prefab: EntityPrefab) -> None:
    """Register a service type for later use.

    Parameters
    ----------
    world
        The world instance to save to service type to.
    prefab
        GameObject prefab information about the service type.
    """

    world.get_resource(GameObjectFactory).add(prefab)
    world.get_resource(ActivityLibrary).activities_to_instantiate.add(prefab.name)
