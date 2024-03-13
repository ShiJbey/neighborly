"""Life Event System.

Life events are the building block of story generation. We set them apart from the
ECS-related events by requiring that each have a timestamp of the in-simulation date
they were emitted. Life events are tracked in two places -- the GlobalEventHistory and
in characters' PersonalEventHistories.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterator

import attrs
import pydantic

from neighborly.datetime import SimDate
from neighborly.ecs import Event


class LifeEventConsideration(pydantic.BaseModel):
    """A consideration rule that calculates how likely a life event is too occur."""

    preconditions: list[str] = pydantic.Field(default_factory=list)
    """Precondition statements."""
    score: int
    """A score to add if the preconditions pass."""


@attrs.define
class LifeEvent(Event, ABC):
    """An event of significant importance in a GameObject's life"""

    timestamp: SimDate
    """The date when this event occurred."""

    @property
    @abstractmethod
    def description(self) -> str:
        """A string description of the event."""
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""

        raise NotImplementedError()


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

    def __iter__(self) -> Iterator[LifeEvent]:
        return self.history.__iter__()

    def __getitem__(self, key: int) -> LifeEvent:
        return self.history[key]
