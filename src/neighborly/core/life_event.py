from __future__ import annotations

import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
)

from neighborly.core.ecs import Component, ISystem, Event, GameObject, IEventListener, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.time import SimDateTime

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
    """Decorator that registers a probability function"""

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


class LifeEvent:
    """
    LifeEvents contain information about occurrences that
    happened in the story world.

    Attributes
    ----------
    name: str
        Name of the event
    timestamp: str
        Timestamp for when the event occurred
    roles: List[EventRole]
        Roles that were involved in this event
    """

    __slots__ = "timestamp", "name", "roles"

    def __init__(self, name: str, timestamp: str, roles: List[EventRole]) -> None:
        self.name: str = name
        self.timestamp: str = timestamp
        self.roles: List[EventRole] = [*roles]

    def get_type(self) -> str:
        """Return the type of this event"""
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "roles": {role.name: role.gid for role in self.roles},
        }

    def __getitem__(self, role_name: str) -> int:
        for role in self.roles:
            if role == role_name:
                return role.gid

    def __repr__(self) -> str:
        return f"LifeEvent(name={self.name}, timestamp={self.timestamp}, roles=[{self.roles}]"

    def __str__(self) -> str:
        return f"{self.name} [at {self.timestamp}] : {', '.join(map(lambda r: f'{r.name}:{r.gid}', self.roles))}"


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
    effect_fn: LifeEventCallback
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


class LifeEventLogger(Component, IEventListener):
    """Records a collection of life events associated with GameObjects"""

    __slots__ = "events"

    def __init__(self) -> None:
        super().__init__()
        self.events: list[LifeEvent] = []

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return LifeEventLogger()

    def will_handle_event(self, event: Event) -> bool:
        return True

    def handle_event(self, event: Event) -> bool:
        if isinstance(event, LifeEvent):
            self.events.append(event)
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "events": [e.to_dict() for e in self.events]}


_CT = TypeVar("_CT")


class EventRole:
    """
    EventRole is a role that has a GameObject bound to it.
    It does not contain any information about filtering for
    the role.

    Attributes
    ----------
    name: str
        Name of the role
    gid: int
        Unique identifier for the GameObject bound to this role
    components: List[Type[Component]]
        Component types associated with this role that are
        associated with the bound GameObject
    """

    __slots__ = "name", "gid", "components"

    def __init__(self, name: str, gid: int, components: List[Type[Component]]) -> None:
        self.name: str = name
        self.gid: int = gid
        self.components: List[Type[Component]] = [*components]


class RoleFilterFn(Protocol):
    """Function that filters GameObjects for an EventRole"""

    def __call__(self, event: LifeEvent, *components: Component) -> bool:
        raise NotImplementedError


class EventRoleType:
    """
    Information about a role within a LifeEvent, and logic
    for how to filter which gameobjects can be bound to the
    role.
    """

    __slots__ = "name", "filter_fn", "components"

    def __init__(
        self,
        name: str,
        components: List[Type[Component]],
        filter_fn: Optional[RoleFilterFn] = None,
    ) -> None:
        self.name: str = name
        self.components: List[Type[Component]] = [*components]
        self.filter_fn: RoleFilterFn = filter_fn if filter_fn else lambda c, e: True

    def fill_role(
        self, world: World, life_event: LifeEvent, candidate: Optional[GameObject] = None
    ) -> Optional[EventRole]:
        """Attempt to fill a role for a LifeEvent"""
        if candidate:
            components = world.ecs.try_components(candidate.id, *self.components)
            if components and self.filter_fn(life_event, *components):
                return EventRole(self.name, candidate.id, self.components)
        else:

            if self.filter_fn is None:
                candidate_list = world.get_components(*self.components)
            else:
                candidate_list = \
                    list(
                        filter(lambda res: self.filter_fn(life_event, *res[1]), world.get_components(*self.components)))

            if any(candidate_list):
                chosen_candidate = world.get_resource(NeighborlyEngine).rng.choice(
                    candidate_list
                )
                return EventRole(self.name, chosen_candidate[0], self.components)

        return None


class LifeEventType:
    """
    User-facing class for implementing behaviors around life events

    This is adapted from:
    https://github.com/ianhorswill/CitySimulator/blob/master/Assets/Codes/Action/Actions/ActionType.cs

    Attributes
    ----------
    name: str
        Name of the LifeEventType and the LifeEvent it instantiates
    roles: List[EventRoleType]
        The roles that need to be cast for this event to be executed
    frequency: int (default: 1)
        The relative frequency of this event compared to other events
    effect_fn: Callable[..., None]

    """

    __slots__ = (
        "name",
        "frequency",
        "roles",
        "effect_fn",
    )

    def __init__(
        self,
        name: str,
        roles: List[EventRoleType],
        frequency: int = 1,
        effect_fn: Optional[Callable[[LifeEvent], None]] = None,
    ) -> None:
        self.name: str = name
        self.roles: List[EventRoleType] = roles
        self.frequency: float = frequency
        self.effect_fn: Optional[Callable[[LifeEvent], None]] = effect_fn

    def instantiate(self, world: World, **kwargs: GameObject) -> Optional[LifeEvent]:
        """Attempts to create a new LifeEvent instance"""
        life_event = LifeEvent(
            self.name,
            world.get_resource(SimDateTime).to_iso_str(),
            []
        )

        for role_type in self.roles:
            bound_object = kwargs.get(role_type.name)
            if bound_object is not None:
                temp = role_type.fill_role(world, life_event, candidate=bound_object)
                if temp is not None:
                    life_event.roles.append(temp)
                else:
                    # Return none if the role candidate is not a fit
                    return None
            else:
                temp = role_type.fill_role(world, life_event)
                if temp is not None:
                    life_event.roles.append(temp)
                else:
                    # Return None if there are no available entities to fill
                    # the current role
                    return None

        return life_event


class EventRoleDatabase:
    _registry: Dict[str, EventRoleType] = {}

    @classmethod
    def register(cls, name: str, event_role_type: EventRoleType) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name] = event_role_type

    @classmethod
    def roles(cls) -> List[EventRoleType]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> EventRoleType:
        """Get a LifeEventType using a name"""
        return cls._registry[name]


class LifeEventDatabase:
    """
    Static class used to store instances of LifeEventTypes for
    use at runtime.
    """

    _registry: Dict[str, LifeEventType] = {}

    @classmethod
    def register(cls, name: str, life_event_type: LifeEventType) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name] = life_event_type

    @classmethod
    def events(cls) -> List[LifeEventType]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> LifeEventType:
        """Get a LifeEventType using a name"""
        return cls._registry[name]


class LifeEventSimulator(ISystem):
    """
    LifeEventSimulator handles firing LifeEvents for characters
    and performing character behaviors

    Attributes
    ----------
    event_history: List[LifeEvent]
        List of events that have occurred over the history of the simulation
    """

    __slots__ = "event_history"

    def __init__(self) -> None:
        super().__init__()
        self.event_history: List[LifeEvent] = []

    def try_execute_event(self, world: World, event_type: LifeEventType) -> None:
        """Execute the given LifeEventType if successfully instantiated"""
        event: LifeEvent = event_type.instantiate(world)
        if event is not None:
            if event_type.effect_fn is not None:
                event_type.effect_fn(event)
            self.event_history.append(event)

    def process(self, *args, **kwargs) -> None:
        """Simulate LifeEvents for characters"""
        rng = self.world.get_resource(NeighborlyEngine).rng
        for event_type in LifeEventDatabase.events():
            if rng.random() < event_type.frequency:
                self.try_execute_event(self.world, event_type)
