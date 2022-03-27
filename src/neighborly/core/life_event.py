from collections import defaultdict
from typing import Any, Callable, Optional, Dict, List, DefaultDict, Iterable, Union

from neighborly.core.ecs import GameObject, Component
from neighborly.core.engine import AbstractFactory, ComponentSpec

PreconditionFn = Callable[..., bool]
EffectFn = Callable[..., None]
ProbabilityFn = Callable[..., float]

_precondition_fn_registry: Dict[str, PreconditionFn] = {}
_effect_fn_registry: Dict[str, EffectFn] = {}
_probability_fn_registry: Dict[str, ProbabilityFn] = {}


def register_precondition(fn: PreconditionFn) -> None:
    """Adds function to the global registry of event preconditions"""
    global _precondition_fn_registry
    _precondition_fn_registry[fn.__name__] = fn


def register_effect(fn: EffectFn) -> None:
    """Adds a function to the global registry of event effects"""
    global _effect_fn_registry
    _effect_fn_registry[fn.__name__] = fn


def register_probability(fn: ProbabilityFn) -> None:
    """Adds a function to the global registry of event probability functions"""
    global _probability_fn_registry
    _probability_fn_registry[fn.__name__] = fn


def get_precondition(name: str) -> PreconditionFn:
    try:
        return _precondition_fn_registry[name]
    except KeyError:
        raise EventPreconditionNotFoundError(name)


def get_effect(name: str) -> EffectFn:
    try:
        return _effect_fn_registry[name]
    except KeyError:
        raise EventEffectNotFoundError(name)


def get_probability(name: str) -> ProbabilityFn:
    try:
        return _probability_fn_registry[name]
    except KeyError:
        raise EventProbabilityNotFoundError(name)


def event_precondition(fn: PreconditionFn) -> PreconditionFn:
    """Decorator registers a precondition function"""
    register_precondition(fn)
    return fn


def event_effect(fn: EffectFn) -> EffectFn:
    """Decorator that registers an effect function"""
    register_effect(fn)
    return fn


def event_probability(fn: ProbabilityFn) -> ProbabilityFn:
    """Decorator that registers a probability function"""
    register_probability(fn)
    return fn


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


class LifeEvent:
    """An event in the life of a character"""

    __slots__ = "_name", "_precondition_fn", "_probability_fn", "_effect_fn"

    def __init__(
            self,
            name: str,
            precondition_fn: Callable[[GameObject], bool],
            effect_fn: Callable[[GameObject, Optional[Dict[str, Any]]], None],
            probability: Union[float, Callable[[GameObject], float]] = 1.0,
    ) -> None:
        self._name: str = name
        self._precondition_fn: Callable[[GameObject], bool] = precondition_fn
        self._effect_fn: Callable[[GameObject, Optional[Dict[str, Any]]], None] = effect_fn
        if isinstance(probability, float):
            self._probability_fn: Callable[[GameObject], float] = lambda gameobject: probability
        else:
            self._probability_fn: Callable[[GameObject], float] = probability

    @property
    def name(self) -> str:
        return self._name

    @property
    def precondition(self) -> Callable[[GameObject], bool]:
        return self._precondition_fn

    @property
    def effect(self) -> Callable[[GameObject, Optional[Dict[str, Any]]], None]:
        return self._effect_fn

    @property
    def probability(self) -> Callable[[GameObject], float]:
        return self._probability_fn


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

    __slots__ = "_event_type", "_time_stamp", "_metadata"

    def __init__(
            self,
            event_type: str,
            time_stamp: str,
            metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._event_type: str = event_type
        self._time_stamp: str = time_stamp
        self._metadata: Dict[str, Any] = {**metadata} if metadata else {}

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def time_stamp(self) -> str:
        return self._time_stamp

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self._event_type,
            'time_stamp': self._time_stamp,
            **self._metadata,
        }

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(type={}, date={}, metadata={})".format(
            self.__class__.__name__,
            self.event_type,
            self.time_stamp,
            self.metadata.__repr__(),
        )


class LifeEventHandler(Component):
    """
    Handles checking a LifeEvent's preconditions and callback effects
    for a single GameObject

    Attributes
    ----------
    preconditions: Dict[str, List[PreconditionFn]]
        Function to check if this event is accepted
    effects: Dict[str, List[EffectFn]]
        Function that performs GameObject archetype-specific affects
    """

    __slots__ = "_preconditions", "_effects"

    def __init__(
            self,
            preconditions: Optional[Dict[str, List[PreconditionFn]]] = None,
            effects: Optional[Dict[str, List[EffectFn]]] = None
    ) -> None:
        super().__init__()
        self._preconditions: DefaultDict[str, List[PreconditionFn]] = defaultdict(list)
        self._effects: DefaultDict[str, List[EffectFn]] = defaultdict(list)

        if preconditions:
            self._preconditions.update(preconditions)
        if effects:
            self._effects.update(effects)

    @property
    def preconditions(self) -> Dict[str, List[PreconditionFn]]:
        return self._preconditions

    @property
    def effects(self) -> Dict[str, List[EffectFn]]:
        return self._effects

    def run_effects(self, event: str) -> None:
        """Execute all the effect functions for an event"""
        map(lambda fn: fn(self.gameobject), self.effects[event])

    def check_preconditions(self, event: str) -> bool:
        """Return True if all the preconditions for an event pass"""
        return all([fn(self.gameobject) for fn in self._preconditions[event]])

    def add_precondition(self, event: str, *condition_name: str) -> None:
        """Add one or more preconditions to the given event"""
        for name in condition_name:
            try:
                self._preconditions[event].append(_precondition_fn_registry[name])
            except KeyError:
                raise EventPreconditionNotFoundError(name)

    def add_effect(self, event: str, *effect_name: str) -> None:
        """Add one or more effects to the given event"""
        for name in effect_name:
            try:
                self._effects[event].append(_effect_fn_registry[name])
            except KeyError:
                raise EventEffectNotFoundError(name)


class LifeEventHandlerFactory(AbstractFactory):
    """Factory for creating LifeEventHandler instances"""

    def __init__(self):
        super().__init__("LifeEventHandler")

    def create(self, spec: ComponentSpec) -> LifeEventHandler:

        preconditions: DefaultDict[str, List[PreconditionFn]] = defaultdict()
        effects: DefaultDict[str, List[EffectFn]] = defaultdict()

        for event, event_config in spec.get_attributes().items():
            if 'preconditions' in event_config:
                for name in event_config['preconditions']:
                    preconditions[event].append(get_precondition(name))
            if 'effects' in event_config:
                for name in event_config['preconditions']:
                    effects[event].append(get_effect(name))

        return LifeEventHandler(preconditions, effects)


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
