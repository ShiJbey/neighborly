from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, Dict, List, Protocol

from neighborly import World


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
    roles: List[neighborly.core.life_event.EventRole]
        GameObjects involved with this event
    metadata: Dict[str, Any]
        Additional information about this event
    _sorted_roles: Dict[str, List[EventRole]]
        (Internal us only) Roles divided by name since there may
        be multiple of the same role present
    """

    __slots__ = "timestamp", "name", "roles", "metadata", "_sorted_roles"

    def __init__(
        self, name: str, timestamp: str, roles: List[EventRole], **kwargs
    ) -> None:
        self.name: str = name
        self.timestamp: str = timestamp
        self.roles: List[EventRole] = []
        self.metadata: Dict[str, Any] = {**kwargs}
        self._sorted_roles: Dict[str, List[EventRole]] = {}
        for role in roles:
            self.add_role(role)

    def add_role(self, role: EventRole) -> None:
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

    def __le__(self, other: Event) -> bool:
        return self.timestamp <= other.timestamp

    def __lt__(self, other: Event) -> bool:
        return self.timestamp < other.timestamp

    def __ge__(self, other: Event) -> bool:
        return self.timestamp >= other.timestamp

    def __gt__(self, other: Event) -> bool:
        return self.timestamp > other.timestamp

    def __repr__(self) -> str:
        return "LifeEvent(name={}, timestamp={}, roles=[{}], metadata={})".format(
            self.name, self.timestamp, self.roles, self.metadata
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


class EventEffectFn(Protocol):
    """Callback function called when an event is executed"""

    def __call__(self, world: World, event: Event) -> None:
        raise NotImplementedError


class EventProbabilityFn(Protocol):
    """Function called to determine the probability of an event executing"""

    def __call__(self, world: World, event: Event) -> float:
        raise NotImplementedError


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
    )

    def __init__(self) -> None:
        self.event_history: List[Event] = []
        self._per_gameobject: DefaultDict[int, List[Event]] = defaultdict(list)
        self._subscribers: List[Callable[[Event], None]] = []
        self._per_gameobject_subscribers: DefaultDict[
            int, List[Callable[[Event], None]]
        ] = defaultdict(list)

    def record_event(self, event: Event) -> None:
        """
        Adds a LifeEvent to the history and calls all registered callback functions

        Parameters
        ----------
        event: Event
            Event that occurred
        """
        self.event_history.append(event)

        for role in event.roles:
            self._per_gameobject[role.gid].append(event)
            if role.gid in self._per_gameobject_subscribers:
                for cb in self._per_gameobject_subscribers[role.gid]:
                    cb(event)

        for cb in self._subscribers:
            cb(event)

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
