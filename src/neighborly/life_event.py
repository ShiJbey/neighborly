"""Life Event System.

Life events are the building block of story generation. We set them apart from the
ECS-related events by requiring that each have a timestamp of the in-simulation date
they were emitted. Life events are tracked in two places -- the GlobalEventHistory and
in characters' PersonalEventHistories.

"""

from __future__ import annotations

import logging
from abc import ABCMeta, abstractmethod
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Type,
    TypeVar,
    cast,
)

import attrs
from ordered_set import OrderedSet

from neighborly.datetime import SimDate
from neighborly.ecs import Component, Event, GameObject, World

_logger = logging.getLogger(__name__)


@attrs.define
class EventRole:
    """A role within a life event that a GameObject is bound to."""

    name: str
    """The name of the role."""
    gameobject: GameObject
    """The GameObject bound to the role."""
    log_event: bool = False
    """Should characters log the event when dispatched."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the role to a JSON-serializable dictionary."""
        return {"name": self.name, "gameobject": self.gameobject.uid}

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.name}: {self.gameobject.name})"


class EventRoleList:
    """A collection of event roles."""

    __slots__ = "_roles", "_sorted_roles"

    _roles: list[EventRole]
    """All the roles within the list."""
    _sorted_roles: dict[str, list[EventRole]]
    """The roles sorted by role name."""

    def __init__(self, roles: Optional[Iterable[EventRole]] = None) -> None:
        """
        Parameters
        ----------
        roles
            The roles to instantiate the list with, by default None
        """
        self._roles = []
        self._sorted_roles = {}

        if roles:
            for role in roles:
                self.add_role(role)

    def add_role(self, role: EventRole) -> None:
        """Add role to the list.

        Parameters
        ----------
        role
            A bound role.
        """
        self._roles.append(role)
        if role.name not in self._sorted_roles:
            self._sorted_roles[role.name] = []
        self._sorted_roles[role.name].append(role)

    def get_all(self, role_name: str) -> tuple[GameObject, ...]:
        """Get all GameObjects bound to the given role name.

        Parameters
        ----------
        role_name
            The name of the role to search for.

        Returns
        -------
        list[GameObject]
            A lis tof all the GameObjects bound to this role name.
        """
        return tuple(role.gameobject for role in self._sorted_roles[role_name])

    def get_first(self, role_name: str) -> GameObject:
        """Get the first GameObject bound to the role name.

        Parameters
        ----------
        role_name
            The name of the role to get from the list.

        Returns
        -------
        GameObject
            The bound GameObject.
        """
        return self._sorted_roles[role_name][0].gameobject

    def get_first_or_none(self, role_name: str) -> Optional[GameObject]:
        """Get the GameObject bound to the role name.

        Parameters
        ----------
        role_name
            The name of the role to get from the list.

        Returns
        -------
        GameObject or None
            The bound GameObject or None if no role exists.
        """
        if role_name in self._sorted_roles:
            return self._sorted_roles[role_name][0].gameobject
        return None

    def __len__(self) -> int:
        return len(self._roles)

    def __bool__(self) -> bool:
        return bool(self._roles)

    def __getitem__(self, role_name: str) -> GameObject:
        return self.get_first(role_name)

    def __iter__(self) -> Iterator[EventRole]:
        return iter(self._roles)

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return str(self._roles)


_ET_contra = TypeVar("_ET_contra", bound="LifeEvent", contravariant=True)


@attrs.define
class _EventConsiderationWrapper(Generic[_ET_contra]):
    """Wraps an event consideration function for use in metaclass construction."""

    fn: Callable[[_ET_contra], float]

    def __call__(self, event: _ET_contra) -> float:
        return self.fn(event)


def event_consideration(fn: Callable[[_ET_contra], float]):
    """A decorator to indicate that a static method is an event consideration."""

    return _EventConsiderationWrapper(fn)


class LifeEventMeta(ABCMeta):
    """A Metaclass that helps simplify random event definitions."""

    _considerations: tuple[_EventConsiderationWrapper[LifeEvent], ...]
    """Consideration functions for calculating an event's probability of occurring."""

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs: Any,
    ):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        LifeEventMeta._detect_considerations(cls)
        return cls

    def _detect_considerations(cls: type) -> None:
        """Detect static methods that use the event_consideration decorator.

        Parameters
        ----------
        cls
            The class to process
        """
        considerations: list[_EventConsiderationWrapper[Any]] = []

        # Check the existing probability modifiers in base classes
        for base_class in cls.__bases__:
            for entry in getattr(base_class, "considerations", []):
                if isinstance(entry, _EventConsiderationWrapper):
                    considerations.append(cast(_EventConsiderationWrapper[Any], entry))

        # Check the declared probability modifiers
        for attr_name, attr_value in cls.__dict__.items():
            if isinstance(attr_value, staticmethod):
                attr = getattr(cls, attr_name)
                if isinstance(attr, _EventConsiderationWrapper):
                    considerations.append(cast(_EventConsiderationWrapper[Any], attr))

        # Set combined collection of event roles for the given type
        setattr(cls, "_considerations", tuple(considerations))


class LifeEvent(Event, metaclass=LifeEventMeta):
    """An event of significant importance in a GameObject's life"""

    base_probability: ClassVar[float] = 0.5
    """The probability of the event happening, independent of considerations."""
    _considerations: tuple[_EventConsiderationWrapper[LifeEvent], ...]
    """Consideration functions for calculating an event's probability of occurring."""

    __slots__ = ("_timestamp", "_roles", "_data")

    _timestamp: SimDate
    """The date when this event occurred."""
    _roles: EventRoleList
    """The bound roles for this life event."""
    _data: dict[str, Any]
    """Event data aside from roles."""

    def __init__(
        self,
        world: World,
        roles: Iterable[EventRole],
        **kwargs: Any,
    ) -> None:
        super().__init__(world)
        self._timestamp = world.resource_manager.get_resource(SimDate).copy()
        self._roles = EventRoleList(roles)
        self._data = {**kwargs}

    @property
    def timestamp(self) -> SimDate:
        """Get the timestamp for when this event occurred."""
        return self._timestamp

    @property
    def roles(self) -> EventRoleList:
        """Get the list of the event's roles."""
        return self._roles

    @property
    def data(self) -> Mapping[str, Any]:
        """Get data dict."""
        return self._data

    @abstractmethod
    def execute(self) -> None:
        """Logic to be executed when the event is dispatched."""
        return

    @classmethod
    @abstractmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> Optional[LifeEvent]:
        """Attempt to create a new instance of the life event.

        Parameters
        ----------
        subject
            The GameObject that the event is happening to. This is usually a character.

        Returns
        -------
        LifeEvent or None
            An instance of the life event if all required information is found.
        """
        raise NotImplementedError()

    def get_probability(self) -> float:
        """Get the probability of an event instance occurring."""
        cumulative_score: float = self.base_probability
        consideration_count: int = 1

        external_considerations = self.world.resource_manager.get_resource(
            EventConsiderations
        ).get_event_considerations(type(self))

        all_considerations: list[Callable[[LifeEvent], float]] = [
            *type(self)._considerations,
            *external_considerations,
        ]

        for consideration in all_considerations:
            consideration_score = consideration(self)

            # Scores greater than zero are added to the cumulative score
            if consideration_score > 0:
                cumulative_score += consideration_score
                consideration_count += 1

            # Scores equal to zero make the entire score zero (make zero a veto value)
            elif consideration_score == 0.0:
                cumulative_score = 0.0
                break

        # Scores are averaged using the arithmetic mean
        final_score = cumulative_score / consideration_count

        return final_score

    def dispatch(self, log_event: bool = True) -> None:
        super().dispatch()

        if log_event:
            for role in self._roles:
                if role.log_event:
                    role.gameobject.get_component(PersonalEventHistory).append(self)

            self.world.resource_manager.get_resource(GlobalEventHistory).append(self)
            _logger.info("[%s] %s", str(self.timestamp), str(self))

        self.execute()

    def to_dict(self) -> dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            **super().to_dict(),
            "timestamp": str(self._timestamp),
            "roles": [r.to_dict() for r in self._roles],
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, timestamp={self.timestamp} "
            f"role={repr(self.roles)})"
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"


class PersonalEventHistory(Component):
    """Stores a record of all past events for a specific GameObject."""

    __slots__ = ("_history",)

    _history: list[LifeEvent]
    """A list of events in chronological-order."""

    def __init__(self) -> None:
        super().__init__()
        self._history = []

    @property
    def history(self) -> Iterable[LifeEvent]:
        """A collection of events in chronological-order."""
        return self._history

    def append(self, event: LifeEvent) -> None:
        """Record a new life event.

        Parameters
        ----------
        event
            The event to record.
        """
        self._history.append(event)

    def to_dict(self) -> dict[str, Any]:
        return {"events": [e.event_id for e in self._history]}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        history = [f"{type(e).__name__}({e.event_id})" for e in self._history]
        return f"{self.__class__.__name__}({history})"


class EventConsiderations:
    """A shared collection of third-party event considerations."""

    _considerations_by_type: dict[
        Type[LifeEvent], OrderedSet[Callable[[LifeEvent], float]]
    ]
    """Event listeners that are only called when a specific type of event fires."""

    def __init__(self) -> None:
        self._considerations_by_type = {}

    def add_consideration(
        self,
        event_type: Type[_ET_contra],
        consideration_fn: Callable[[_ET_contra], float],
    ) -> None:
        """Add a consideration to the collection.

        Parameters
        ----------
        event_type
            The event type the consideration is for
        consideration_fn
            The function with the consideration logic
        """
        if event_type not in self._considerations_by_type:
            self._considerations_by_type[event_type] = OrderedSet([])

        self._considerations_by_type[event_type].add(
            cast(Callable[[LifeEvent], float], consideration_fn)
        )

    def get_event_considerations(
        self, event_type: Type[_ET_contra]
    ) -> Iterable[Callable[[_ET_contra], float]]:
        """Get all considerations for a given type.

        Parameters
        ----------
        event_type
            The event type to get considerations for.

        Returns
        -------
        Iterable[Callable[[_ET_contra], float]]
            All the added considerations for this event type
        """
        considerations = cast(
            Iterable[Callable[[_ET_contra], float]],
            self._considerations_by_type.get(event_type, OrderedSet([])),
        )

        return considerations


class GlobalEventHistory:
    """Stores a record of all past life events."""

    __slots__ = ("_history",)

    _history: dict[int, LifeEvent]
    """All recorded life events mapped to their event ID."""

    def __init__(self) -> None:
        self._history = {}

    def append(self, event: LifeEvent) -> None:
        """Record a new life event.

        Parameters
        ----------
        event
            The event to record.
        """
        self._history[event.event_id] = event

    def to_dict(self) -> dict[str, Any]:
        """Serialize object into JSON-serializable dict."""
        return {str(key): entry.to_dict() for key, entry in self._history.items()}

    def __iter__(self) -> Iterator[LifeEvent]:
        return self._history.values().__iter__()

    def __getitem__(self, key: int) -> LifeEvent:
        return self._history[key]
