"""Life Event System.

Life events are the building block of story generation. We set them apart from the
ECS-related events by requiring that each have a timestamp of the in-simulation date
they were emitted. Life events are tracked in two places -- the GlobalEventHistory and
in characters' PersonalEventHistories.

"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from itertools import count
from typing import Any, ClassVar, Iterable

from neighborly.datetime import SimDate
from neighborly.ecs import Component, Event, GameObject, World

_logger = logging.getLogger(__name__)


class LifeEvent(Event, ABC):
    """An event of significant importance in a GameObject's life"""

    __event_type__: str = ""
    """ID used to map the event to considerations and listeners"""

    _next_life_event_id: ClassVar[count[int]] = count()

    __slots__ = ("life_event_id", "timestamp")

    life_event_id: int
    """Numerical ID of this life event."""
    timestamp: SimDate
    """The timestamp of the event"""

    def __init__(self, world: World) -> None:
        if not type(self).__event_type__:
            raise ValueError(f"Please specify __event_id__ for class {type(self)}")
        super().__init__(self.__event_type__, world)
        self.life_event_id = next(self._next_life_event_id)
        self.timestamp = world.resources.get_resource(SimDate).copy()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.life_event_id}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r})"
        )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.life_event_id}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r})"
        )

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize event data to a dict."""
        return {
            "life_event_id": self.life_event_id,
            "event_type": self.event_type,
            "timestamp": str(self.timestamp),
        }


class PersonalEventHistory(Component):
    """Stores a record of all past events for a specific GameObject."""

    __slots__ = ("_history",)

    _history: list[LifeEvent]
    """A list of events in chronological-order."""

    def __init__(self, gameobject: GameObject) -> None:
        super().__init__(gameobject)
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
        return {"events": [e.to_dict() for e in self._history]}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        history = [f"{type(e).__name__}({e.life_event_id})" for e in self._history]
        return f"{self.__class__.__name__}({history})"


class GlobalEventHistory:
    """Stores a record of all past life events."""

    __slots__ = ("history",)

    history: list[LifeEvent]
    """All recorded life events mapped to their event ID."""

    def __init__(self) -> None:
        self.history = []

    def append(self, event: LifeEvent) -> None:
        """Record a new life event.

        Parameters
        ----------
        event
            The event to record.
        """
        self.history.append(event)

    def to_dict(self) -> dict[str, Any]:
        """Serialize object into JSON-serializable dict."""
        return {"events": [e.to_dict() for e in self.history]}


def dispatch_life_event(world: World, event: LifeEvent) -> None:
    """Dispatch a life event."""

    world.resources.get_resource(GlobalEventHistory).append(event)

    _logger.info("[%s]: %s", str(event.timestamp), str(event))

    world.events.dispatch_event(event)


def add_to_personal_history(gameobject: GameObject, event: LifeEvent) -> None:
    """Add a life event to a GameObject's personal history."""

    gameobject.get_component(PersonalEventHistory).append(event)
