from __future__ import annotations

from abc import ABC
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Type, Callable,
)

from neighborly.core.ecs import Component, ISystem, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.time import SimDateTime


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

    def __init__(self, name: str, timestamp: str, roles: List[EventRole], **kwargs) -> None:
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
            "roles": {role.name: role.gid for role in self.roles},
        }

    def __getitem__(self, role_name: str) -> int:
        for role in self.roles:
            if role.name == role_name:
                return role.gid
        raise KeyError(role_name)

    def __repr__(self) -> str:
        return f"LifeEvent(name={self.name}, timestamp={self.timestamp}, roles=[{self.roles}], metadata={self.metadata})"

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


class RoleFilterFn(Protocol):
    """Function that filters GameObjects for an EventRole"""

    def __call__(self, world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        raise NotImplementedError


class AbstractEventRoleType(ABC):
    """
    Abstract base class for defining roles that
    GameObjects can be bound to when executing
    LifeEvents
    """

    __slots__ = "name", "components"

    def __init__(self, name: str, components: List[Type[Component]]) -> None:
        self.name: str = name
        self.components: List[Type[Component]] = components

    def fill_role(
        self, world: World, life_event: LifeEvent, candidate: Optional[GameObject] = None
    ) -> Optional[EventRole]:
        """
        Attempt to fill a role for a LifeEvent

        **Do Not Override this method unless absolutely necessary**
        """
        if candidate:
            if candidate.has_component(*self.components) and self.filter(world, life_event, candidate):
                return EventRole(self.name, candidate.id)
        else:
            candidate_list = \
                list(
                    filter(lambda res: self.filter(world, life_event, world.get_gameobject(res[0])),
                           world.get_components(*self.components)))

            if any(candidate_list):
                chosen_candidate = world.get_resource(NeighborlyEngine).rng.choice(
                    candidate_list
                )
                return EventRole(self.name, chosen_candidate[0])

        return None

    def filter(self, world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        """Return True if the game object meets the conditions to fill this role"""
        return True


class EventRoleType(AbstractEventRoleType):
    """
    Information about a role within a LifeEvent, and logic
    for how to filter which gameobjects can be bound to the
    role.
    """

    __slots__ = "filter_fn"

    def __init__(
        self,
        name: str,
        components: List[Type[Component]],
        filter_fn: Optional[RoleFilterFn] = None,
    ) -> None:
        super().__init__(name, components)
        self.filter_fn: RoleFilterFn = filter_fn if filter_fn else lambda w, e, g: True

    def filter(self, world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        return self.filter_fn(world, event, gameobject)


class LifeEventEffectFn(Protocol):
    """Callback function called when a life event is executed"""

    def __call__(self, world: World, event: LifeEvent) -> None:
        raise NotImplementedError


class AbstractLifeEventType(ABC):
    """
    Abstract base class for defining LifeEventTypes
    """

    __slots__ = "name", "frequency", "roles"

    def __init__(self, name: str, roles: List[EventRoleType], frequency: int = 1) -> None:
        self.name: str = name
        self.roles: List[EventRoleType] = roles
        self.frequency: float = frequency

    def instantiate(self, world: World, **kwargs: GameObject) -> Optional[LifeEvent]:
        """
        Attempts to create a new LifeEvent instance

        **Do Not Override this method unless absolutely necessary**
        """
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

    def execute(self, world: World, event: LifeEvent) -> None:
        return


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
    frequency: int (default: 1)
        The relative frequency of this event compared to other events
    execute_fn: Callable[..., None]
        Function that executes changes to the world state base don the event
    """

    __slots__ = "execute_fn"

    def __init__(
        self,
        name: str,
        roles: List[EventRoleType],
        frequency: int = 1,
        execute_fn: Optional[LifeEventEffectFn] = None,
    ) -> None:
        super().__init__(name, roles, frequency)
        self.execute_fn: Optional[LifeEventEffectFn] = execute_fn

    def execute(self, world: World, event: LifeEvent) -> None:
        self.execute_fn(world, event)


class EventRoles:
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


class LifeEvents:
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

    def try_execute_event(self, world: World, event_type: LifeEventType) -> None:
        """Execute the given LifeEventType if successfully instantiated"""
        event: LifeEvent = event_type.instantiate(world)
        if event is not None:
            if event_type.execute_fn is not None:
                event_type.execute_fn(world, event)
            world.get_resource(LifeEventLog).record_event(event)

    def process(self, *args, **kwargs) -> None:
        """Simulate LifeEvents for characters"""
        rng = self.world.get_resource(NeighborlyEngine).rng
        for event_type in LifeEvents.events():
            if rng.random() < event_type.frequency:
                self.try_execute_event(self.world, event_type)
