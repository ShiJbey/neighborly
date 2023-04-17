from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Type

from neighborly.core.ecs import Component, Event, GameObject, World
from neighborly.core.roles import Role, RoleList
from neighborly.core.ecs.ecs import ISerializable
from neighborly.core.time import SimDateTime


class LifeEvent(Event, ABC):
    """An event of significant importance in a GameObject's life"""

    _next_event_id: int = 0

    __slots__ = "_roles", "_timestamp", "_uid"

    def __init__(
        self,
        timestamp: SimDateTime,
        roles: Iterable[Role],
    ) -> None:
        """
        Parameters
        ----------
        timestamp: SimDateTime
            Timestamp for when this event
        roles: Iterable[Role]
            The names of roles mapped to GameObjects
        """
        self._uid: int = LifeEvent._next_event_id
        LifeEvent._next_event_id += 1
        self._timestamp: SimDateTime = timestamp.copy()
        self._roles: RoleList = RoleList(roles)

    def get_id(self) -> int:
        return self._uid

    def get_timestamp(self) -> SimDateTime:
        return self._timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            "type": self.get_type(),
            "timestamp": str(self._timestamp),
            "roles": {role.name: role.gameobject.uid for role in self._roles},
        }

    def iter_roles(self) -> Iterator[Role]:
        return self._roles.__iter__()

    def __getitem__(self, role_name: str) -> GameObject:
        return self._roles[role_name]

    def __repr__(self) -> str:
        return "{}(timestamp={}, roles=[{}])".format(
            self.get_type(), str(self.get_timestamp()), self._roles
        )

    def __str__(self) -> str:
        return "{} [@ {}] {}".format(
            self.get_type(),
            str(self.get_timestamp()),
            ", ".join([str(role) for role in self._roles]),
        )

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, LifeEvent):
            return self._uid == __o._uid
        raise TypeError(f"Expected type Event, but was {type(__o)}")

    def __le__(self, other: LifeEvent) -> bool:
        return self._uid <= other._uid

    def __lt__(self, other: LifeEvent) -> bool:
        return self._uid < other._uid

    def __ge__(self, other: LifeEvent) -> bool:
        return self._uid >= other._uid

    def __gt__(self, other: LifeEvent) -> bool:
        return self._uid > other._uid


class ActionableLifeEvent(LifeEvent):
    """
    User-facing class for implementing behaviors around life events

    This is adapted from:
    https://github.com/ianhorswill/CitySimulator/blob/master/Assets/Codes/Action/Actions/ActionType.cs
    """

    __slots__ = "_roles"

    def __init__(
        self,
        timestamp: SimDateTime,
        roles: Iterable[Role],
    ) -> None:
        """
        Parameters
        ----------
        timestamp: SimDateTime
            Timestamp for when this event
        roles: Dict[str, GameObject
            The names of roles mapped to GameObjects
        """
        super().__init__(timestamp, roles)

    @abstractmethod
    def get_probability(self) -> float:
        """Get the probability of an instance of this event happening

        Returns
        -------
        float
            The probability of the event given the GameObjects bound
            to the roles in the LifeEventInstance
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self) -> None:
        """Executes the LifeEvent instance, emitting an event"""
        raise NotImplementedError

    def is_valid(self, world: World) -> bool:
        """Check that all gameobjects still meet the preconditions for their roles"""
        return self.instantiate(world, bindings=self._roles) is not None

    @classmethod
    @abstractmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        """Attempts to create a new LifeEvent instance

        Parameters
        ----------
        world: World
            Neighborly world instance
        bindings: Dict[str, GameObject], optional
            Suggested bindings of role names mapped to GameObjects

        Returns
        -------
        LifeEventInstance or None
            An instance of this life event if all roles are bound successfully
        """
        raise NotImplementedError


class RandomLifeEvents:
    """Static class used to store LifeEvents that can be triggered randomly"""

    _registry: Dict[str, Type[ActionableLifeEvent]] = {}

    @classmethod
    def add(cls, life_event_type: Type[ActionableLifeEvent]) -> None:
        """Register a new random LifeEvent type"""
        cls._registry[life_event_type.__name__] = life_event_type

    @classmethod
    def pick_one(cls, rng: random.Random) -> Type[ActionableLifeEvent]:
        """
        Return a random registered random life event

        Parameters
        ----------
        rng: random.Random
            A random number generator

        Returns
        -------
        Type[ActionableLifeEvent]
            A randomly-chosen random event from the registry
        """
        return rng.choice(list(cls._registry.values()))

    @classmethod
    def get_size(cls) -> int:
        """Return number of registered random life events"""
        return len(cls._registry)


class EventHistory(Component):
    """Stores a record of all past events for a specific GameObject"""

    __slots__ = "_history"

    def __init__(self) -> None:
        super().__init__()
        self._history: List[LifeEvent] = []

    def append(self, event: LifeEvent) -> None:
        self._history.append(event)

    def __iter__(self) -> Iterator[LifeEvent]:
        return self._history.__iter__()

    def to_dict(self) -> Dict[str, Any]:
        return {"events": [e.get_id() for e in self._history]}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            [f"{type(e).__name__}({e.get_id()})" for e in self._history],
        )


class AllEvents(ISerializable):
    """Stores a record of all past events"""

    _event_listeners: List[Callable[[LifeEvent], None]] = []

    __slots__ = "_history"

    def __init__(self) -> None:
        super().__init__()
        self._history: Dict[int, LifeEvent] = {}

    def append(self, event: LifeEvent) -> None:
        self._history[event.get_id()] = event
        for cb in self._event_listeners:
            cb(event)

    def to_dict(self) -> Dict[str, Any]:
        return {str(key): entry.to_dict() for key, entry in self._history.items()}

    def __iter__(self) -> Iterator[LifeEvent]:
        return self._history.values().__iter__()

    @classmethod
    def on_event(cls, listener: Callable[[LifeEvent], None]) -> None:
        cls._event_listeners.append(listener)
