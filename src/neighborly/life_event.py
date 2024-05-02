"""Life Event System.

Life events are the building block of story generation. We set them apart from the
ECS-related events by requiring that each have a timestamp of the in-simulation date
they were emitted. Life events are tracked in two places -- the GlobalEventHistory and
in characters' PersonalEventHistories.

"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from sqlalchemy.orm import Mapped, mapped_column

from neighborly.datetime import SimDate
from neighborly.ecs import Component, GameData, GameObject, World

_logger = logging.getLogger(__name__)


class LifeEvent(GameData):
    """An event of significant importance in a GameObject's life"""

    __tablename__ = "life_events"

    __event_type__: str = ""
    """ID used to map the event to considerations and listeners"""

    event_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp_str: Mapped[str] = mapped_column(name="timestamp")
    type: Mapped[str]
    world: World
    timestamp: SimDate

    __mapper_args__ = {
        "polymorphic_identity": "life_event",
        "polymorphic_on": "type",
    }

    __allow_unmapped__ = True

    def __init__(self, world: World) -> None:
        super().__init__()
        self.timestamp = world.resources.get_resource(SimDate).copy()
        self.timestamp_str = str(self.timestamp)

    @property
    def event_type(self) -> str:
        """A type name for the event."""

        return self.type

    @classmethod
    def get_event_id(cls) -> str:
        """Get the event ID for this event type."""
        if not cls.__event_type__:
            raise ValueError(f"Please specify __event_id__ for class {cls}")
        return cls.__event_type__

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r})"
        )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize event data to a dict."""
        return {
            "event_id": self.event_id,
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
        return {"events": [e.event_id for e in self._history]}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        history = [f"{type(e).__name__}({e.event_id})" for e in self._history]
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

    # This needs to be called before we do anything because adding it to the session
    # assigns the "event_id" attribute.
    with world.session() as session:
        session.add(event)

    world.resources.get_resource(GlobalEventHistory).append(event)

    _logger.info("[%s]: %s", event.timestamp_str, str(event))

    world.events.dispatch_event(event)


def add_to_personal_history(gameobject: GameObject, event: LifeEvent) -> None:
    """Add a life event to a GameObject's personal history."""

    gameobject.get_component(PersonalEventHistory).append(event)
