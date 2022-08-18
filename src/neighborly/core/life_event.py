from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Type

from neighborly.core.ecs import Component, GameObject, ISystem, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.core.town import Town


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

    __slots__ = "timestamp", "name", "roles", "metadata"

    def __init__(
        self, name: str, timestamp: str, roles: List[EventRole], **kwargs
    ) -> None:
        self.name: str = name
        self.timestamp: str = timestamp
        self.roles: List[EventRole] = [*roles]
        self.metadata: Dict[str, Any] = {**kwargs}

    def get_type(self) -> str:
        """Return the type of this event"""
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "roles": [role.to_dict() for role in self.roles],
        }

    def __getitem__(self, role_name: str) -> int:
        for role in self.roles:
            if role.name == role_name:
                return role.gid
        raise KeyError(role_name)

    def __repr__(self) -> str:
        return "LifeEvent(name={}, timestamp={}, roles=[{}], metadata={})".format(
            self.name, self.timestamp, self.roles, self.metadata
        )

    def __str__(self) -> str:
        return f"{self.name} [at {self.timestamp}] : {', '.join(map(lambda r: f'{r.name}:{r.gid}', self.roles))}"


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
    """

    __slots__ = "name", "gid"

    def __init__(self, name: str, gid: int) -> None:
        self.name: str = name
        self.gid: int = gid

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "gid": self.gid}


class RoleBinderFn(Protocol):
    """Callable that returns a GameObject that meets requirements for a given Role"""

    def __call__(self, world: World, event: LifeEvent) -> Optional[GameObject]:
        raise NotImplementedError


class RoleFilterFn(Protocol):
    """Function that filters GameObjects for an EventRole"""

    def __call__(self, world: World, gameobject: GameObject, **kwargs) -> bool:
        raise NotImplementedError


def join_filters(*filters: RoleFilterFn) -> RoleFilterFn:
    """Joins a bunch of filters into one function"""

    def fn(world: World, gameobject: GameObject, **kwargs) -> bool:
        return all([f(world, gameobject, **kwargs) for f in filters])

    return fn


def or_filters(
    *preconditions: RoleFilterFn,
) -> RoleFilterFn:
    """Only one of the given preconditions has to pass to return True"""

    def wrapper(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        for p in preconditions:
            if p(world, gameobject, **kwargs):
                return True
        return False

    return wrapper


class AbstractEventRoleType(ABC):
    """
    Abstract base class for defining roles that
    GameObjects can be bound to when executing
    LifeEvents
    """

    __slots__ = "name"

    def __init__(self, name: str) -> None:
        self.name: str = name

    @abstractmethod
    def fill_role(self, world: World, event: LifeEvent) -> Optional[EventRole]:
        """Find a GameObject to bind to this role given the event"""
        raise NotImplementedError

    @abstractmethod
    def fill_role_with(
        self, world: World, event: LifeEvent, candidate: GameObject
    ) -> Optional[EventRole]:
        """Attempt to bind the candidate GameObject to this role given the event"""
        raise NotImplementedError


class EventRoleType(AbstractEventRoleType):
    """
    Information about a role within a LifeEvent, and logic
    for how to filter which gameobjects can be bound to the
    role.
    """

    __slots__ = "binder_fn", "components", "filter_fn"

    def __init__(
        self,
        name: str,
        components: List[Type[Component]] = None,
        filter_fn: Optional[RoleFilterFn] = None,
        binder_fn: Optional[RoleBinderFn] = None,
    ) -> None:
        super().__init__(name)
        self.components: List[Type[Component]] = components if components else []
        self.filter_fn: Optional[RoleFilterFn] = filter_fn
        self.binder_fn: Optional[RoleBinderFn] = binder_fn

    def fill_role(
        self,
        world: World,
        event: LifeEvent,
    ) -> Optional[EventRole]:

        if self.binder_fn is not None:
            obj = self.binder_fn(world, event)
            return EventRole(self.name, obj.id) if obj is not None else None

        candidate_list: List[int] = list(
            map(
                lambda entry: entry[0],
                filter(
                    lambda res: self.filter_fn(
                        world, world.get_gameobject(res[0]), event=event
                    )
                    if self.filter_fn
                    else True,
                    world.get_components(*self.components),
                ),
            )
        )

        if any(candidate_list):
            chosen_candidate = world.get_resource(NeighborlyEngine).rng.choice(
                candidate_list
            )
            return EventRole(self.name, chosen_candidate)

        return None

    def fill_role_with(
        self,
        world: World,
        event: LifeEvent,
        candidate: GameObject,
    ) -> Optional[EventRole]:
        if candidate.has_component(*self.components):
            if self.filter_fn and self.filter_fn(world, candidate, event=event):
                return EventRole(self.name, candidate.id)
            else:
                return EventRole(self.name, candidate.id)

        return None


class LifeEventEffectFn(Protocol):
    """Callback function called when a life event is executed"""

    def __call__(self, world: World, event: LifeEvent) -> EventResult:
        raise NotImplementedError


class AbstractLifeEventType(ABC):
    """
    Abstract base class for defining LifeEventTypes
    """

    __slots__ = "name", "probability", "roles"

    def __init__(
        self, name: str, roles: List[EventRoleType], frequency: float = 1.0
    ) -> None:
        self.name: str = name
        self.roles: List[EventRoleType] = roles
        self.probability: float = frequency

    def instantiate(self, world: World, **kwargs: GameObject) -> Optional[LifeEvent]:
        """
        Attempts to create a new LifeEvent instance

        **Do Not Override this method unless absolutely necessary**
        """
        life_event = LifeEvent(
            self.name, world.get_resource(SimDateTime).to_iso_str(), []
        )

        for role_type in self.roles:
            bound_object = kwargs.get(role_type.name)
            if bound_object is not None:
                temp = role_type.fill_role_with(
                    world, life_event, candidate=bound_object
                )
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

    def execute(self, world: World, event: LifeEvent) -> None:
        return


@dataclass
class EventResult:
    generated_events: List[LifeEvent] = field(default_factory=list)


class LifeEventType(AbstractLifeEventType):
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
    probability: int (default: 1)
        The relative frequency of this event compared to other events
    execute_fn: Callable[..., None]
        Function that executes changes to the world state base don the event
    """

    __slots__ = "execute_fn"

    def __init__(
        self,
        name: str,
        roles: List[EventRoleType],
        probability: float = 1.0,
        execute_fn: Optional[LifeEventEffectFn] = None,
    ) -> None:
        super().__init__(name, roles, probability)
        self.execute_fn: Optional[LifeEventEffectFn] = execute_fn

    def execute(self, world: World, event: LifeEvent) -> None:
        self.execute_fn(world, event)


class EventRoleLibrary:
    _registry: Dict[str, EventRoleType] = {}

    @classmethod
    def add(cls, name: str, event_role_type: EventRoleType) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name] = event_role_type

    @classmethod
    def get_all(cls) -> List[EventRoleType]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> EventRoleType:
        """Get a LifeEventType using a name"""
        return cls._registry[name]


class LifeEventLibrary:
    """
    Static class used to store instances of LifeEventTypes for
    use at runtime.
    """

    _registry: Dict[str, LifeEventType] = {}

    @classmethod
    def add(cls, life_event_type: LifeEventType, name: str = None) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name if name else life_event_type.name] = life_event_type

    @classmethod
    def get_all(cls) -> List[LifeEventType]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> LifeEventType:
        """Get a LifeEventType using a name"""
        return cls._registry[name]


class LifeEventLog:
    """
    Global resource for storing and accessing LifeEvents
    """

    __slots__ = "event_history", "_subscribers"

    def __init__(self) -> None:
        self.event_history: List[LifeEvent] = []
        self._subscribers: List[Callable[[LifeEvent], None]] = []

    def record_event(self, event: LifeEvent) -> None:
        self.event_history.append(event)
        for cb in self._subscribers:
            cb(event)

    def subscribe(self, cb: Callable[[LifeEvent], None]) -> None:
        self._subscribers.append(cb)

    def unsubscribe(self, cb: Callable[[LifeEvent], None]) -> None:
        self._subscribers.remove(cb)


class LifeEventSimulator(ISystem):
    """
    LifeEventSimulator handles firing LifeEvents for characters
    and performing character behaviors
    """

    __slots__ = "interval", "next_trigger"

    def __init__(self, interval: TimeDelta = None) -> None:
        super().__init__()
        self.interval: TimeDelta = interval if interval else TimeDelta(days=14)
        self.next_trigger: SimDateTime = SimDateTime()

    def try_execute_event(self, world: World, event_type: LifeEventType) -> None:
        """Execute the given LifeEventType if successfully instantiated"""
        event: LifeEvent = event_type.instantiate(world)
        if event is not None:
            if event_type.execute_fn is not None:
                result = event_type.execute_fn(world, event)
                for e in result.generated_events:
                    world.get_resource(LifeEventLog).record_event(e)

    def process(self, *args, **kwargs) -> None:
        """Simulate LifeEvents for characters"""
        date = self.world.get_resource(SimDateTime)

        if date < self.next_trigger:
            return
        else:
            self.next_trigger = date.copy() + self.interval

        town = self.world.get_resource(Town)
        rng = self.world.get_resource(NeighborlyEngine).rng

        # Perform number of events equal to 10% of the population
        for _ in range(town.population // 10):
            event_type = rng.choice(LifeEventLibrary.get_all())
            if rng.random() < event_type.probability:
                self.try_execute_event(self.world, event_type)

        # for event_type in LifeEvents.events():
        #     if rng.random() < event_type.probability:
        #         self.try_execute_event(self.world, event_type)
