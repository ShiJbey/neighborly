from __future__ import annotations
import logging

from collections import defaultdict
from dataclasses import dataclass
from abc import ABC, abstractclassmethod, abstractmethod
from typing import (
    Any,
    Callable,
    Generator,
    Dict,
    Tuple,
    List,
    Generic,
    Iterable,
    Optional,
    Protocol,
    TypeVar,
)

from neighborly.core.ecs import GameObject, World

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


class IProbabilityFn(Protocol):
    """Callable that produces a probability [0.0, 1.0] of a event firing"""

    def __call__(self, gameobject: GameObject, **kwargs) -> float:
        raise NotImplementedError()


class ILifeEventCallback(Protocol):
    def __call__(self, gameobject: GameObject, event: LifeEvent) -> bool:
        raise NotImplementedError


@dataclass
class _EventCallbackDbEntry(Generic[_T]):
    """
    A single entry within the event callback database

    Attributes
    ----------
    fn: _T
        Either a Precondition, Effect, or Probability function
    description: str
        Short description of what the function does
    """

    fn: _T
    description: str


class EventCallbackDatabase:
    """Manages the various callback functions available when constructing events"""

    _precondition_db: Dict[str, _EventCallbackDbEntry[ILifeEventCallback]] = {}
    _effect_db: Dict[str, _EventCallbackDbEntry[ILifeEventCallback]] = {}
    _probability_db: Dict[str, _EventCallbackDbEntry[IProbabilityFn]] = {}

    @classmethod
    def register_precondition(
        cls, name: str, fn: ILifeEventCallback, description: Optional[str] = None
    ) -> None:
        """Adds function to the global registry of event preconditions"""
        cls._precondition_db[name] = _EventCallbackDbEntry(
            fn, description if description else ""
        )

    @classmethod
    def register_effect(
        cls, name: str, fn: ILifeEventCallback, description: Optional[str] = None
    ) -> None:
        """Adds a function to the global registry of event effects"""
        cls._effect_db[name] = _EventCallbackDbEntry(
            fn, description if description else ""
        )

    @classmethod
    def register_probability(
        cls, name: str, fn: IProbabilityFn, description: Optional[str] = None
    ) -> None:
        """Adds a function to the global registry of event probability functions"""
        cls._probability_db[name] = _EventCallbackDbEntry(
            fn, description if description else ""
        )

    @classmethod
    def get_precondition(cls, name: str) -> ILifeEventCallback:
        try:
            return cls._precondition_db[name].fn
        except KeyError:
            raise EventPreconditionNotFoundError(name)

    @classmethod
    def get_effect(cls, name: str) -> ILifeEventCallback:
        try:
            return cls._effect_db[name].fn
        except KeyError:
            raise EventEffectNotFoundError(name)

    @classmethod
    def get_probability(cls, name: str) -> IProbabilityFn:
        try:
            return cls._probability_db[name].fn
        except KeyError:
            raise EventProbabilityNotFoundError(name)


def event_precondition(name: str, description: Optional[str] = None):
    """Decorator registers a precondition function"""

    def wrapper(fn: ILifeEventCallback):
        EventCallbackDatabase.register_precondition(name, fn, description)
        return fn

    return wrapper


def event_effect(name: str, description: Optional[str] = None):
    """Decorator that registers an effect function"""

    def wrapper(fn: ILifeEventCallback):
        EventCallbackDatabase.register_effect(name, fn, description)
        return fn

    return wrapper


def event_probability(name: str, description: Optional[str] = None):
    """Decorator that registers an probability function"""

    def wrapper(fn: IProbabilityFn):
        EventCallbackDatabase.register_probability(name, fn, description)
        return fn

    return wrapper


class EventPreconditionNotFoundError(Exception):
    """Event Raised when a precondition's name is not found in the library"""

    def __init__(self, name: str) -> None:
        super().__init__(f"Precondition with name '{name}' not found")
        self.message: str = f"Precondition with name '{name}' not found"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return self.message


class EventEffectNotFoundError(Exception):
    """Event Raised when a post-effect's name is not found in the library"""

    def __init__(self, name: str) -> None:
        super().__init__(f"Post-Effect with name '{name}' not found")
        self.message: str = f"Post-Effect with name '{name}' not found"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return self.message


class EventProbabilityNotFoundError(Exception):
    """Event Raised when a probability function is not found in the library"""

    def __init__(self, name: str) -> None:
        super().__init__(f"Probability function with name '{name}' not found")
        self.message: str = f"Probability function with name '{name}' not found"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return self.message


class LifeEvent(ABC):
    """
    Events are things that happen in the story world that GameObjects
    can react to.


    Events allow neighborly to decouple the simulation logic from any
    GameObject-specific logic that should run as a response. Events are
    blocking. They are handled immediately by event handlers when available.
    """

    __slots__ = "timestamp"

    def __init__(self, timestamp: str) -> None:
        super().__init__()
        self.timestamp: str = timestamp

    @abstractclassmethod
    def get_type(cls) -> str:
        """Return the type of this event"""
        raise NotImplementedError()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {"event_type": self.get_type(), "timestamp": self.timestamp}


class IPatternFn(Protocol):
    @abstractmethod
    def __call__(
        self, world: World, **kwargs
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        raise NotImplementedError()


class LifeEventRule:
    """
    An event that happens to a gameobject in the world. This may be used to represent
    life events for characters, social interactions, business events, etc.

    Attributes
    ----------
    name: str
        Name of the event used when checking event handlers
    description: str
        A short description of this rule
    pattern_fn: IPatternFn
        A precondition function that needs to return True for the event to fire
    effect: LifeEventCallback
        An effect function that runs if the event fires
    probability: float
        A functions that returns the probability of the event firing
    """

    __slots__ = (
        "name",
        "pattern_fn",
        "probability",
        "effect_fn",
        "description",
    )

    def __init__(
        self,
        name: str,
        pattern_fn: IPatternFn,
        effect_fn: Optional[Callable[[World], None]] = None,
        probability: float = 1.0,
        description: str = "",
    ) -> None:
        self.name: str = name
        self.pattern_fn: IPatternFn = pattern_fn
        self.effect_fn: Optional[Callable[[World], None]] = effect_fn
        self.probability: float = probability
        self.description: str = description


class LifeEventHandler:
    """
    Collection of precondition and effect callback associated with a specific event type

    Attributes
    ----------
    preconditions: list[LifeEventCallback]
        precondition callback functions
    effects: list[LifeEventCallback]
        effect callback functions
    """

    __slots__ = "preconditions", "effects"

    def __init__(self) -> None:
        self.preconditions: list[ILifeEventCallback] = []
        self.effects: list[ILifeEventCallback] = []

    def check_preconditions(self, gameobject: GameObject, event: LifeEvent) -> bool:
        """Return True if all the preconditions for an event pass"""
        if self.preconditions:
            return all([fn(gameobject, event) for fn in self.preconditions])
        return True

    def handle_event(self, gameobject: GameObject, event: LifeEvent) -> None:
        """Run the effect callbacks associated with this event"""
        for fn in self.effects:
            fn(gameobject, event)

    def add_precondition(self, fn: ILifeEventCallback) -> None:
        """Add one or more preconditions to the given event"""
        self.preconditions.append(fn)

    def add_effect(self, fn: ILifeEventCallback) -> None:
        """Add one or more effects to the given event"""
        self.effects.append(fn)


class LifeEventLogger:
    """Records a collection of life events associated with GameObjects"""

    __slots__ = "_events", "_game_objects", "_next_event_id", "_subscribers"

    def __init__(self) -> None:
        self._next_event_id: int = 0
        self._events: list[LifeEvent] = []
        self._game_objects: defaultdict[int, list[int]] = defaultdict(lambda: list())
        self._subscribers: Dict[int, List[Callable[[int, LifeEvent], None]]] = {}

    def log_event(self, event: LifeEvent, gameobject_ids: Iterable[int]) -> None:
        """Add an event to the record of all events and associate it with character"""
        self._events.append(event)

        for gid in gameobject_ids:
            self._game_objects[gid].append(self._next_event_id)
            if gid in self._subscribers:
                map(lambda f: f(gid, event), self._subscribers[gid])

        logger.debug(str(event))

        self._next_event_id += 1

    def get_all_events(self) -> List[LifeEvent]:
        """Get all recorded events"""
        return self._events

    def get_events_for(self, gid: int) -> List[LifeEvent]:
        """Get all the life events for a game object"""
        return [self._events[i] for i in self._game_objects[gid]]

    def subscribe_to_gameobject(
        self, gid: int, fn: Callable[[int, LifeEvent], None]
    ) -> None:
        if gid not in self._subscribers:
            self._subscribers[gid] = []
        self._subscribers[gid].append(fn)


class ILifeEventListener(ABC):
    """Abstract interface that components inherit from when they want to listen for events"""

    @abstractmethod
    def check_preconditions(self, event: LifeEvent) -> bool:
        """
        Check the preconditions for this event type to see if they pass

        Returns
        -------
        bool
            True if the event passes all the preconditions
        """
        raise NotImplementedError()

    @abstractmethod
    def handle_event(self, event: LifeEvent) -> bool:
        """
        Perform logic when an event occurs

        Returns
        -------
        bool
            True if the event was handled successfully
        """
        raise NotImplementedError()


def check_gameobject_preconditions(gameobject: GameObject, event: LifeEvent) -> bool:
    """Return True if the given gameobject accepts the event"""
    for c in gameobject.get_components():
        if isinstance(c, ILifeEventListener):
            if not c.check_preconditions(event):
                return False
    return True


def handle_gameobject_effects(gameobject: GameObject, event: LifeEvent) -> bool:
    """Return True if the given gameobject accepts the event"""
    for c in gameobject.get_components():
        if isinstance(c, ILifeEventListener):
            c.handle_event(event)
    return True
