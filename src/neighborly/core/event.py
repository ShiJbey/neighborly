from __future__ import annotations

from abc import ABC
from collections import defaultdict
from typing import Any, DefaultDict, Dict, Iterator, List, Type, TypeVar

from neighborly.core.ecs import Component
from neighborly.core.serializable import ISerializable
from neighborly.core.time import SimDateTime


class Event(ABC):
    """Events signal when things happen in the simulation

    Event listener systems use event to know when something about the simulations state
    has changed.
    """

    __slots__ = "_timestamp", "_uid"

    _next_event_id: int = 0

    def __init__(self, timestamp: SimDateTime) -> None:
        self._uid: int = Event._next_event_id
        Event._next_event_id += 1
        self._timestamp: SimDateTime = timestamp.copy()

    def get_id(self) -> int:
        return self._uid

    def get_type(self) -> str:
        return self.__class__.__name__

    def get_timestamp(self) -> SimDateTime:
        return self._timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {"type": self.get_type(), "timestamp": str(self._timestamp)}

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Event):
            return self._uid == other._uid
        raise TypeError(f"Expected type Event, but was {type(other)}")

    def __le__(self, other: Event) -> bool:
        return self._uid <= other._uid

    def __lt__(self, other: Event) -> bool:
        return self._uid < other._uid

    def __ge__(self, other: Event) -> bool:
        return self._uid >= other._uid

    def __gt__(self, other: Event) -> bool:
        return self._uid > other._uid

    def __repr__(self) -> str:
        return "{}(id={}, timestamp={})".format(
            self.__class__.__name__,
            self._uid,
            str(self._timestamp),
        )

    def __str__(self) -> str:
        return f"{self.get_type()} [at {str(self._timestamp)}]"


_ET = TypeVar("_ET", bound=Event)


class EventBuffer:
    """Manages all the events that have occurred in the simulation during a timestep"""

    __slots__ = (
        "_event_buffers_by_type",
        "_event_buffer",
    )

    def __init__(self) -> None:
        self._event_buffers_by_type: DefaultDict[
            Type[Event], List[Event]
        ] = defaultdict(list)
        self._event_buffer: List[Event] = []

    def iter_events(self) -> Iterator[Event]:
        """Return an iterator to all the events in the buffer regardless of type"""
        return self._event_buffer.__iter__()

    def iter_events_of_type(self, event_type: Type[_ET]) -> Iterator[_ET]:
        """Return an iterator to the buffer of events for the given type"""
        # We probably shouldn't ignore this typing error, but I don't
        # know how to solve this right now
        return self._event_buffers_by_type[event_type].__iter__()  # type: ignore

    def append(self, event: Event) -> None:
        """Add a new event to the buffer

        Parameters
        ----------
        event: Event
            An event instance
        """
        self._event_buffer.append(event)
        self._event_buffers_by_type[type(event)].append(event)

    def clear(self) -> None:
        """Clears all events from the buffer"""
        self._event_buffer.clear()
        self._event_buffers_by_type.clear()


class EventHistory(Component):
    """Stores a record of all past events for a specific GameObject"""

    __slots__ = "_history"

    def __init__(self) -> None:
        super().__init__()
        self._history: List[Event] = []

    def append(self, event: Event) -> None:
        self._history.append(event)

    def __iter__(self) -> Iterator[Event]:
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

    __slots__ = "_history"

    def __init__(self) -> None:
        super().__init__()
        self._history: Dict[int, Event] = {}

    def append(self, event: Event) -> None:
        self._history[event.get_id()] = event

    def to_dict(self) -> Dict[str, Any]:
        return {str(key): entry.to_dict() for key, entry in self._history.items()}

    def __iter__(self) -> Iterator[Event]:
        return self._history.values().__iter__()
