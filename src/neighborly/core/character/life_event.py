from typing import Callable, Dict, List, Optional
from dataclasses import dataclass

import esper


@dataclass(frozen=True)
class LifeEvent:
    name: str
    description: str
    preconditions: Callable[[esper.World, int], bool]
    post_effects: Callable[[esper.World, int], None]


# These are the event types that may be created
# by character behaviors, social practices, and
# statuses. This validity set helps to expose
# event_type typos in downstream code
_valid_event_types: Dict[str, LifeEvent] = {}


def register_event_type(event: LifeEvent) -> None:
    """Adds an event type name to the set of valid event types"""
    _valid_event_types[event.name] = event


class LifeEventRecord:
    """Record of a major event that occurred in a character's life

    Attributes
    ----------
    event_type: str
        What type of life event this is (e.g. married, started dating,
        birth of child, work promotion, ...)
    time_stamp: str
        When did this event occur. This value should enable us to
        lexicographically sort events by time_stamp
    metadata: Dict[str, str]
        Additional information about this event
    """

    __slots__ = "event_type", "time_stamp", "metadata"

    def __init__(
        self,
        event_type: str,
        time_stamp: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        self.event_type: str = event_type
        self.time_stamp: str = time_stamp
        self.metadata: Dict[str, str] = metadata if metadata else {}

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}<{}>(date={}, metadata={})".format(
            self.__class__.__name__,
            self.event_type,
            self.time_stamp,
            self.metadata.__repr__(),
        )


class CharacterLifeEvents:
    """Collection of all of a character's major life events

    Attributes
    ----------
    _history: List[LifeEvent]
        List of this character's life events
    """

    __slots__ = "_history"

    def __init__(self) -> None:
        self._history: List[LifeEventRecord] = []

    @property
    def history(self) -> List[LifeEventRecord]:
        return self._history

    def __repr__(self) -> str:
        return "{}(history={})".format(
            self.__class__.__name__, self._history.__repr__()
        )
