from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Protocol

from neighborly.core.ecs import GameObject, World


class RoleList:
    """A collection of roles for an event"""

    __slots__ = "_roles", "_sorted_roles"

    def __init__(self, roles: Optional[List[EventRole]] = None) -> None:
        self._roles: List[EventRole] = []
        self._sorted_roles: Dict[str, List[EventRole]] = {}

        if roles:
            for role in roles:
                self.add_role(role)

    @property
    def roles(self) -> List[EventRole]:
        return self._roles

    def add_role(self, role: EventRole) -> None:
        """Add role to the event"""
        self._roles.append(role)
        if role.name not in self._sorted_roles:
            self._sorted_roles[role.name] = []
        self._sorted_roles[role.name].append(role)

    def get_all(self, role_name: str) -> List[int]:
        """Return the IDs of all GameObjects bound to the given role name"""
        return list(map(lambda role: role.gid, self._sorted_roles[role_name]))

    def __getitem__(self, role_name: str) -> int:
        return self._sorted_roles[role_name][0].gid

    def __iter__(self):
        return self._roles.__iter__()


class Event:
    """
    LifeEvents contain information about occurrences that
    happened in the story world.

    Attributes
    ----------
    name: str
        Name of the event
    timestamp: str
        Timestamp for when the event occurred
    roles: RoleList
        GameObjects involved with this event
    """

    __slots__ = "timestamp", "name", "roles"

    def __init__(self, name: str, timestamp: str, roles: List[EventRole]) -> None:
        self.name: str = name
        self.timestamp: str = timestamp
        self.roles: RoleList = RoleList(roles)

    def add_role(self, role: EventRole) -> None:
        """Add role to the event"""
        self.roles.add_role(role)

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

    def get_all(self, role_name: str) -> List[int]:
        """Return the IDs of all GameObjects bound to the given role name"""
        return self.roles.get_all(role_name)

    def __getitem__(self, role_name: str) -> int:
        return self.roles[role_name]

    def __le__(self, other: Event) -> bool:
        return self.timestamp <= other.timestamp

    def __lt__(self, other: Event) -> bool:
        return self.timestamp < other.timestamp

    def __ge__(self, other: Event) -> bool:
        return self.timestamp >= other.timestamp

    def __gt__(self, other: Event) -> bool:
        return self.timestamp > other.timestamp

    def __repr__(self) -> str:
        return "LifeEvent(name={}, timestamp={}, roles=[{}])".format(
            self.name, self.timestamp, self.roles
        )

    def __str__(self) -> str:
        return f"{self.name} [at {self.timestamp}] : {', '.join(map(lambda r: f'{r.name}:{r.gid}', self.roles))}"


class EventRole:
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


class EventLog:
    """
    Global resource that manages all the LifeEvents that have occurred in the simulation.

    This component should always be present in the simulation.

    Attributes
    ----------
    event_history: List[Event]
        All the events that have occurred thus far in the simulation
    _per_gameobject: DefaultDict[int, List[Event]]
        Dictionary of all the LifEvents that have occurred divided by participant ID
    _subscribers: List[Callable[[LifeEvent], None]]
        Callback functions executed everytime a LifeEvent occurs
    _per_gameobject_subscribers: DefaultDict[int, List[Callable[[LifeEvent], None]]
        Callback functions divided by the GameObject to which they are subscribed
    """

    __slots__ = (
        "event_history",
        "_subscribers",
        "_per_gameobject",
        "_per_gameobject_subscribers",
        "_listeners",
        "_event_queue",
    )

    def __init__(self) -> None:
        self.event_history: List[Event] = []
        self._per_gameobject: DefaultDict[int, List[Event]] = defaultdict(list)
        self._subscribers: List[Callable[[Event], None]] = []
        self._per_gameobject_subscribers: DefaultDict[
            int, List[Callable[[Event], None]]
        ] = defaultdict(list)
        self._listeners: DefaultDict[
            str, List[Callable[[World, Event], None]]
        ] = defaultdict(list)
        self._event_queue: List[Event] = []

    def record_event(self, event: Event) -> None:
        """
        Adds a LifeEvent to the history and calls all registered callback functions

        Parameters
        ----------
        event: Event
            The event that occurred
        """
        self.event_history.append(event)
        self._event_queue.append(event)

    def process_event_queue(self, world: World) -> None:
        while self._event_queue:
            event = self._event_queue.pop(0)

            for role in event.roles:
                self._per_gameobject[role.gid].append(event)
                if role.gid in self._per_gameobject_subscribers:
                    for cb in self._per_gameobject_subscribers[role.gid]:
                        cb(event)

            for cb in self._subscribers:
                cb(event)

            for listener in self._listeners[event.name]:
                listener(world, event)

    def on(self, event_name: str, listener: Callable[[World, Event], None]) -> None:
        self._listeners[event_name].append(listener)

    def subscribe(self, cb: Callable[[Event], None]) -> None:
        """
        Add a function to be called whenever a LifeEvent occurs

        Parameters
        ----------
        cb: Callable[[LifeEvent], None]
            Function to call
        """
        self._subscribers.append(cb)

    def unsubscribe(self, cb: Callable[[Event], None]) -> None:
        """
        Remove a function from being called whenever a LifeEvent occurs

        Parameters
        ----------
        cb: Callable[[LifeEvent], None]
            Function to call
        """
        self._subscribers.remove(cb)

    def subscribe_to_gameobject(self, gid: int, cb: Callable[[Event], None]) -> None:
        """
        Add a function to be called whenever the gameobject with the given gid
        is involved in a LifeEvent

        Parameters
        ----------
        gid: int
            ID of the GameObject to subscribe to

        cb: Callable[[LifeEvent], None]
            Callback function executed when a life event occurs
        """
        self._per_gameobject_subscribers[gid].append(cb)

    def unsubscribe_from_gameobject(
        self, gid: int, cb: Callable[[Event], None]
    ) -> None:
        """
        Remove a function from being called whenever the gameobject with the given gid
        is involved in a LifeEvent

        Parameters
        ----------
        gid: int
            ID of the GameObject to subscribe to

        cb: Callable[[LifeEvent], None]
            Callback function executed when a life event occurs
        """
        if gid in self._per_gameobject_subscribers:
            self._per_gameobject_subscribers[gid].remove(cb)

    def get_events_for(self, gid: int) -> List[Event]:
        """
        Get all the LifeEvents where the GameObject with the given gid played a role

        Parameters
        ----------
        gid: int
            ID of the GameObject to retrieve events for

        Returns
        -------
        List[Event]
            Events recorded for the given GameObject
        """
        return self._per_gameobject[gid]


class RoleBinder(Protocol):
    """Function used to fill a RoleList"""

    def __call__(
        self, world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[RoleList]:
        raise NotImplementedError


class EventRoleType:
    """
    Information about a role within a LifeEvent, and logic
    for how to filter which gameobjects can be bound to the
    role.
    """

    __slots__ = "binder_fn", "name"

    def __init__(
        self,
        name: str,
        binder_fn: Optional[RoleTypeBindFn] = None,
    ) -> None:
        self.name: str = name
        self.binder_fn: Optional[RoleTypeBindFn] = binder_fn

    def fill_role(
        self, world: World, roles: RoleList, candidate: Optional[GameObject] = None
    ) -> Optional[EventRole]:

        if self.binder_fn is None:
            if candidate is None:
                return None
            else:
                return EventRole(self.name, candidate.id)

        if gameobject := self.binder_fn(world, roles, candidate):
            return EventRole(self.name, gameobject.id)

        return None


class RoleTypeBindFn(Protocol):
    """Callable that returns a GameObject that meets requirements for a given Role"""

    def __call__(
        self, world: World, roles: RoleList, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        raise NotImplementedError
