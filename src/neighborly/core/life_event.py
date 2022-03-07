from collections import defaultdict
from typing import Any, Callable, Optional, Dict, List, DefaultDict, Iterable

from neighborly.core.ecs import GameObject


class LifeEventHandler:
    """
    Handles checking a LifeEvent's preconditions and callback effects
    for a single GameObject

    Attributes
    ----------
    name: str
        Name of the EventHandler
    precondition: (GameObject) -> bool
        Function to check if this event is accepted
    callback:
        Function that performs GameObject archetype-specific affects
    """

    __slots__ = "_name", "_precondition", "_callback"

    def __init__(
            self,
            name: str,
            precondition: Callable[[GameObject, Dict[str, Any]], bool],
            callback: Callable[[GameObject, Optional[Dict[str, Any]]], None]
    ) -> None:
        self._name: str = name
        self._precondition: Callable[[GameObject, Dict[str, Any]], bool] = precondition
        self._callback: Callable[[GameObject, Optional[Dict[str, Any]]], None] = callback

    @property
    def name(self) -> str:
        return self._name

    @property
    def precondition(self) -> Callable[[GameObject, Dict[str, Any]], bool]:
        return self._precondition

    @property
    def callback(self) -> Callable[[GameObject, Optional[Dict[str, Any]]], None]:
        return self._callback


class LifeEvent:
    """An event in the life of a character"""

    __slots__ = "_name", "_precondition", "_probability", "_callback"

    def __init__(
            self,
            name: str,
            precondition: Callable[[GameObject], bool],
            callback: Callable[[GameObject, Optional[Dict[str, Any]]], None],
            probability: float = 1.0,
    ) -> None:
        self._name: str = name
        self._precondition: Callable[[GameObject], bool] = precondition
        self._callback: Callable[[GameObject, Optional[Dict[str, Any]]], None] = callback
        self._probability: float = probability

    @property
    def name(self) -> str:
        return self._name

    @property
    def precondition(self) -> Callable[[GameObject], bool]:
        return self._precondition

    @property
    def callback(self) -> Callable[[GameObject, Optional[Dict[str, Any]]], None]:
        return self._callback

    @property
    def probability(self) -> float:
        return self._probability


class LifeEventRecord:
    """Record of a major event that occurred in a character's life

    Attributes
    ----------
    event_type: str
        What type of life event this is (e.g. married, started dating,
        birth of child, work promotion, Optional[Dict[str, Any]])
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
            metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.event_type: str = event_type
        self.time_stamp: str = time_stamp
        self.metadata: Dict[str, str] = metadata if metadata else {}

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(type={}, date={}, metadata={})".format(
            self.__class__.__name__,
            self.event_type,
            self.time_stamp,
            self.metadata.__repr__(),
        )


class EventLog:
    """Records a collection of life events associated with game objects"""

    __slots__ = "_events", "_game_objects", "_next_event_id"

    def __init__(self) -> None:
        self._next_event_id: int = 0
        self._events: List[LifeEventRecord] = []
        self._game_objects: DefaultDict[int, List[int]] = defaultdict(lambda: list())

    def add_event(self, record: LifeEventRecord, characters: Iterable[int]) -> None:
        """Add an event to the record of all events and associate it with character"""
        self._events.append(record)

        for character_id in characters:
            self._game_objects[character_id].append(self._next_event_id)

        self._next_event_id += 1

    def get_all_events(self) -> List[LifeEventRecord]:
        """Get all recorded events"""
        return self._events

    def get_events_for(self, gid: int) -> List[LifeEventRecord]:
        """Get all the life events for a game object"""
        return [self._events[i] for i in self._game_objects[gid]]
