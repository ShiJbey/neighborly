from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    Union,
)

from neighborly.core.ecs import Component, GameObject, SystemBase, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.serializable import ISerializable
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.core.town import Town

logger = logging.getLogger(__name__)


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
    roles: List[neighborly.core.life_event.Role]
        GameObjects involved with this event
    metadata: Dict[str, Any]
        Additional information about this event
    _sorted_roles: Dict[str, List[Role]]
        (Internal us only) Roles divided by name since there may
        be multiple of the same role present
    """

    __slots__ = "timestamp", "name", "roles", "metadata", "_sorted_roles"

    def __init__(self, name: str, timestamp: str, roles: List[Role], **kwargs) -> None:
        self.name: str = name
        self.timestamp: str = timestamp
        self.roles: List[Role] = []
        self.metadata: Dict[str, Any] = {**kwargs}
        self._sorted_roles: Dict[str, List[Role]] = {}
        for role in roles:
            self.add_role(role)

    def add_role(self, role: Role) -> None:
        """Add role to the event"""
        self.roles.append(role)
        if role.name not in self._sorted_roles:
            self._sorted_roles[role.name] = []
        self._sorted_roles[role.name].append(role)

    def get_type(self) -> str:
        """Return the type of this event"""
        return self.name

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "roles": [role.to_dict() for role in self.roles],
            "metadata": {**self.metadata},
        }

    def get_all(self, role_name: str) -> List[int]:
        """Return the IDs of all GameObjects bound to the given role name"""
        return list(map(lambda role: role.gid, self._sorted_roles[role_name]))

    def __getitem__(self, role_name: str) -> int:
        return self._sorted_roles[role_name][0].gid

    def __repr__(self) -> str:
        return "LifeEvent(name={}, timestamp={}, roles=[{}], metadata={})".format(
            self.name, self.timestamp, self.roles, self.metadata
        )

    def __str__(self) -> str:
        return f"{self.name} [at {self.timestamp}] : {', '.join(map(lambda r: f'{r.name}:{r.gid}', self.roles))}"


class LifeEventEffectFn(Protocol):
    """Callback function called when a life event is executed"""

    def __call__(self, world: World, event: LifeEvent) -> None:
        raise NotImplementedError


class LifeEventProbabilityFn(Protocol):
    """Function called to determine the probability of an event executing"""

    def __call__(self, world: World, event: LifeEvent) -> float:
        raise NotImplementedError


class LifeEventType:
    """
    User-facing class for implementing behaviors around life events

    This is adapted from:
    https://github.com/ianhorswill/CitySimulator/blob/master/Assets/Codes/Action/Actions/ActionType.cs

    Attributes
    ----------
    name: str
        Name of the LifeEventType and the LifeEvent it instantiates
    roles: List[neighborly.core.life_event.RoleType]
        The roles that need to be cast for this event to be executed
    probability: LifeEventProbabilityFn
        The relative frequency of this event compared to other events
    effects: LifeEventEffectFn
        Function that executes changes to the world state base don the event
    """

    __slots__ = "name", "probability", "roles", "effects"

    def __init__(
        self,
        name: str,
        roles: List[RoleType],
        probability: Union[LifeEventProbabilityFn, float],
        effects: Optional[LifeEventEffectFn] = None,
    ) -> None:
        self.name: str = name
        self.roles: List[RoleType] = roles
        self.probability: LifeEventProbabilityFn = (
            constant_probability(probability)
            if type(probability) == float
            else probability
        )
        self.effects: Optional[LifeEventEffectFn] = effects

    def instantiate(self, world: World, **kwargs: GameObject) -> Optional[LifeEvent]:
        """
        Attempts to create a new LifeEvent instance

        Parameters
        ----------
        world: World
            Neighborly world instance
        **kwargs: Dict[str, GameObject]
            Attempted bindings of GameObjects to RoleTypes

        Notes
        -----
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
                    life_event.add_role(temp)
                else:
                    # Return none if the role candidate is not a fit
                    return None
            else:
                temp = role_type.fill_role(world, life_event)
                if temp is not None:
                    life_event.add_role(temp)
                else:
                    # Return None if there are no available entities to fill
                    # the current role
                    return None

        return life_event

    def execute(self, world: World, event: LifeEvent) -> None:
        """Run the effects function using the given event"""
        self.effects(world, event)

    def try_execute_event(self, world: World, **kwargs: GameObject) -> bool:
        """
        Attempt to instantiate and execute this LifeEventType

        Parameters
        ----------
        world: World
            Neighborly world instance
        **kwargs: Dict[str, GameObject]
            Attempted bindings of GameObjects to RoleTypes

        Returns
        -------
        bool
            Returns True if the event is instantiated successfully and executed
        """
        event = self.instantiate(world, **kwargs)
        rng = world.get_resource(NeighborlyEngine).rng
        if event is not None and rng.random() < self.probability(world, event):
            self.execute(world, event)
            return True
        return False


class EventRoleLibrary:
    _registry: Dict[str, RoleType] = {}

    @classmethod
    def add(cls, name: str, event_role_type: RoleType) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name] = event_role_type

    @classmethod
    def get_all(cls) -> List[RoleType]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> RoleType:
        """Get a LifeEventType using a name"""
        return cls._registry[name]


class LifeEventLibrary:
    """
    Static class used to store instances of LifeEventTypes for
    use at runtime.
    """

    _registry: Dict[str, LifeEventType] = {}

    @classmethod
    def add(cls, life_event_type: LifeEventType, name: Optional[str] = None) -> None:
        """Register a new LifeEventType mapped to a name"""
        key_name = name if name else life_event_type.name
        if key_name in cls._registry:
            logger.debug(f"Overwriting LifeEventType: ({key_name})")
        cls._registry[key_name] = life_event_type

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

    __slots__ = "event_history", "_subscribers", "_per_gameobject"

    def __init__(self) -> None:
        self.event_history: List[LifeEvent] = []
        self._per_gameobject: DefaultDict[int, List[LifeEvent]] = defaultdict(list)
        self._subscribers: List[Callable[[LifeEvent], None]] = []

    def record_event(self, event: LifeEvent) -> None:
        self.event_history.append(event)
        for role in event.roles:
            self._per_gameobject[role.gid].append(event)
        for cb in self._subscribers:
            cb(event)

    def subscribe(self, cb: Callable[[LifeEvent], None]) -> None:
        self._subscribers.append(cb)

    def unsubscribe(self, cb: Callable[[LifeEvent], None]) -> None:
        self._subscribers.remove(cb)

    def get_events_for(self, gid: int) -> List[LifeEvent]:
        """
        Get all the LifeEvents where the GameObject with the given gid played a role
        """
        return self._per_gameobject[gid]


class LifeEventSimulator(SystemBase):
    """
    LifeEventSimulator handles firing LifeEvents for characters
    and performing entity behaviors
    """

    __slots__ = "interval", "next_trigger"

    def __init__(self, interval: Optional[TimeDelta] = None) -> None:
        super().__init__()
        self.interval: TimeDelta = interval if interval else TimeDelta(days=14)
        self.next_trigger: SimDateTime = SimDateTime()

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
            event_type.try_execute_event(self.world)


class Role(ISerializable):
    """
    Role is a role that has a GameObject bound to it.
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

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, gid={self.gid})"


class RoleBinderFn(Protocol):
    """Callable that returns a GameObject that meets requirements for a given Role"""

    def __call__(self, world: World, event: LifeEvent) -> Optional[GameObject]:
        raise NotImplementedError


class RoleFilterFn(Protocol):
    """Function that filters GameObjects for an EventRole"""

    def __call__(self, world: World, gameobject: GameObject, **kwargs) -> bool:
        raise NotImplementedError


class RoleTypeBase(ABC):
    """
    Abstract base class for defining roles that
    GameObjects can be bound to when executing
    LifeEvents

    Attributes
    ----------
    name:
    """

    __slots__ = "name"

    def __init__(self, name: str) -> None:
        self.name: str = name

    @abstractmethod
    def fill_role(self, world: World, event: LifeEvent) -> Optional[Role]:
        """Find a GameObject to bind to this role given the event"""
        raise NotImplementedError

    @abstractmethod
    def fill_role_with(
        self, world: World, event: LifeEvent, candidate: GameObject
    ) -> Optional[Role]:
        """Attempt to bind the candidate GameObject to this role given the event"""
        raise NotImplementedError


class RoleType(RoleTypeBase):
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
    ) -> Optional[Role]:

        if self.binder_fn is not None:
            obj = self.binder_fn(world, event)
            return Role(self.name, obj.id) if obj is not None else None

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
            return Role(self.name, chosen_candidate)

        return None

    def fill_role_with(
        self,
        world: World,
        event: LifeEvent,
        candidate: GameObject,
    ) -> Optional[Role]:
        has_components = (
            candidate.has_component(*self.components) if self.components else True
        )

        passes_filter = (
            self.filter_fn(world, candidate, event=event) if self.filter_fn else True
        )

        return (
            Role(self.name, candidate.id) if has_components and passes_filter else None
        )


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


def constant_probability(probability: float) -> LifeEventProbabilityFn:
    def fn(world: World, event: LifeEvent) -> float:
        return probability

    return fn
