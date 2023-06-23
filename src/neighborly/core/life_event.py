from __future__ import annotations

import dataclasses
import random
from abc import ABC, ABCMeta, abstractmethod
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Tuple, )

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, Event, GameObject, ISerializable, World
from neighborly.core.time import SimDateTime


class EventRole:
    """A role that a GameObject is bound to."""

    __slots__ = "_name", "_gameobject"

    _name: str
    """The name of the role."""

    _gameobject: GameObject
    """The GameObject bound to the role."""

    def __init__(self, name: str, gameobject: GameObject) -> None:
        """
        Parameters
        ----------
        name
            The name of the role
        gameobject
            The GameObject bound to this role
        """
        self._name = name
        self._gameobject = gameobject

    @property
    def name(self) -> str:
        """The name of the role."""
        return self._name

    @property
    def gameobject(self) -> GameObject:
        """The GameObject bound to the role."""
        return self._gameobject

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "gameobject": self.gameobject.uid}

    def __str__(self) -> str:
        return f"({self.name}: {self.gameobject})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, gid={self.gameobject})"


class EventRoleList:
    """A collection of Roles."""

    __slots__ = "_roles", "_sorted_roles"

    _roles: List[EventRole]
    """All the roles within the list."""

    _sorted_roles: Dict[str, List[EventRole]]
    """The roles sorted by role name."""

    def __init__(self, roles: Optional[Iterable[EventRole]] = None) -> None:
        """
        Parameters
        ----------
        roles
            Roles to instantiate the list with, by default None
        """
        self._roles = []
        self._sorted_roles = {}

        if roles:
            for role in roles:
                self.add_role(role)

    def add_role(self, role: EventRole) -> None:
        """Add role to the list.

        Parameters
        ----------
        role
            A bound role.
        """
        self._roles.append(role)
        if role.name not in self._sorted_roles:
            self._sorted_roles[role.name] = []
        self._sorted_roles[role.name].append(role)

    def get_all(self, role_name: str) -> List[GameObject]:
        """Get all GameObjects bound to the given role name.

        Parameters
        ----------
        role_name
            The name of the role to search for.

        Returns
        -------
        List[GameObject]
            A lis tof all the GameObjects bound to this role name.
        """
        return [role.gameobject for role in self._sorted_roles[role_name]]

    def get_first(self, role_name: str) -> GameObject:
        """Get the first GameObject bound to the role name.

        Parameters
        ----------
        role_name
            The name of the role to get from the list.

        Returns
        -------
        GameObject
            The bound GameObject.
        """
        return self._sorted_roles[role_name][0].gameobject

    def get_first_or_none(self, role_name: str) -> Optional[GameObject]:
        """Get the GameObject bound to the role name.

        Parameters
        ----------
        role_name
            The name of the role to get from the list.

        Returns
        -------
        GameObject or None
            The bound GameObject or None if no role exists.
        """
        if role_name in self._sorted_roles:
            return self._sorted_roles[role_name][0].gameobject
        return None

    def __len__(self) -> int:
        return len(self._roles)

    def __bool__(self) -> bool:
        return bool(self._roles)

    def __getitem__(self, role_name: str) -> GameObject:
        return self.get_first(role_name)

    def __iter__(self) -> Iterator[EventRole]:
        return self._roles.__iter__()

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "[{}]".format(", ".join([str(role) for role in self._roles]))


class LifeEvent(Event, ABC):
    """An event of significant importance in a GameObject's life"""

    _next_event_id: int = 0

    __slots__ = "_roles", "_timestamp", "_uid"

    def __init__(
        self,
        timestamp: SimDateTime,
        roles: Iterable[EventRole],
    ) -> None:
        """
        Parameters
        ----------
        timestamp
            Timestamp for when this event
        roles
            The names of roles mapped to GameObjects
        """
        self._uid: int = LifeEvent._next_event_id
        LifeEvent._next_event_id += 1
        self._timestamp: SimDateTime = timestamp.copy()
        self._roles: EventRoleList = EventRoleList(roles)

    @property
    def event_id(self) -> int:
        return self._uid

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp

    @property
    def roles(self) -> EventRoleList:
        return self._roles

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            "type": self.get_type(),
            "timestamp": str(self._timestamp),
            "roles": [role.to_dict() for role in self._roles],
        }

    def __getitem__(self, role_name: str) -> GameObject:
        return self._roles.get_first(role_name)

    def __repr__(self) -> str:
        return "{}(timestamp={}, roles=[{}])".format(
            self.get_type(), str(self.timestamp), self._roles
        )

    def __str__(self) -> str:
        return "{} [@ {}] {}".format(
            self.get_type(),
            str(self.timestamp),
            ", ".join([str(role) for role in self._roles]),
        )

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, LifeEvent):
            return self._uid == __o._uid
        raise TypeError(f"Expected type Event, but was {type(__o)}")

    def __le__(self, other: LifeEvent) -> bool:
        return self._uid <= other._uid

    def __lt__(self, other: LifeEvent) -> bool:
        return self._uid < other._uid

    def __ge__(self, other: LifeEvent) -> bool:
        return self._uid >= other._uid

    def __gt__(self, other: LifeEvent) -> bool:
        return self._uid > other._uid


@dataclasses.dataclass()
class EventRoleBindingContext:
    """Manages information related to the current state of cast roles."""

    world: World
    """The world instance that the GameObjects in the role list belong to."""

    bindings: Optional[EventRoleList] = dataclasses.field(default_factory=EventRoleList)
    """The current set of casted roles."""


EventRoleBindingGeneratorFn = Callable[
    [EventRoleBindingContext], Generator[tuple[GameObject, ...], None, None]
]
"""Role casting functions yield GameObjects to bind to a role."""

_T = TypeVar("_T", bound=LifeEvent)


class EventRoleConsideration(Protocol):
    """A consideration function for evaluating the probability of a GameObject taking on a role in a life event."""

    def __call__(self, gameobject: GameObject, event: _T) -> Optional[float]:
        raise NotImplementedError()


class EventRoleConsiderationList(List[EventRoleConsideration], Generic[_T]):
    """A collection of considerations associated with an event role."""

    def calculate_score(self, gameobject: GameObject, event: _T) -> float:
        """Scores each consideration for a GameObject and returns the aggregate score.

        Parameters
        ----------
        gameobject
            A GameObject.
        event
            The event to consider.

        Returns
        -------
        float
            The aggregate consideration score.
        """

        cumulative_score: float = 1.0
        consideration_count: int = 0

        for c in self:
            consideration_score = c(gameobject, event)
            if consideration_score is not None:
                assert 0.0 <= consideration_score <= 1.0
                cumulative_score *= consideration_score
                consideration_count += 1

            if cumulative_score == 0.0:
                break

        if consideration_count == 0:
            consideration_count = 1
            cumulative_score = 0.0

        # Scores are averaged using the Geometric Mean instead of
        # arithmetic mean. It calculates the mean of a product of
        # n-numbers by finding the n-th root of the product
        # Tried using the averaging scheme by Dave Mark, but it
        # returned values that felt too small and were not easy
        # to reason about.
        # Using this method, a cumulative score of zero will still
        # result in a final score of zero.

        final_score = cumulative_score ** (1 / consideration_count)

        return final_score


class EventRoleInfo:
    """Information about an event role.

    These are created when the @event_role decorator is used within a random life event class definition.
    It defines the name of the role, a generator that produces potential bindings, and considerations for
    GameObjects that are bound to the role.
    """

    __slots__ = "name", "binding_fn", "considerations"

    name: str
    """The name of the role."""

    binding_fn: EventRoleBindingGeneratorFn
    """The function used to bind GameObject instances to the role."""

    considerations: EventRoleConsiderationList[Any]
    """A list of considerations for GameObjects bound to this role."""

    def __init__(
        self,
        name: str,
        binding_fn: EventRoleBindingGeneratorFn,
        considerations: EventRoleConsiderationList[Any],
    ) -> None:
        self.name = name
        self.binding_fn = binding_fn
        self.considerations = considerations

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name})"


def event_role(
    name: str = "", considerations: Optional[EventRoleConsiderationList] = None
):
    """A decorator to indicate that a function is for casting a role"""

    def event_role_decorator(fn):
        return EventRoleInfo(
            name if name else fn.__name__,
            fn,
            EventRoleConsiderationList(considerations if considerations else []),
        )

    return event_role_decorator


class RandomLifeEventMeta(ABCMeta):
    """A Metaclass that helps simplify random event definitions."""

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs: Any,
    ):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        _update_roles(cls)
        return cls


def _update_roles(cls: type) -> None:
    """
    Updates the internal records of event roles for classes that derive from the
    RandomEventMeta metaclass.

    Parameters
    ----------
    cls
        The class type to process

    Notes
    -----
    This function is modeled after the update_abstractmethods function in abc.py
    """
    event_roles: List[EventRoleInfo] = []

    # Check the existing event role methods of the parents
    for base_class in cls.__bases__:
        for entry in getattr(base_class, "__event_roles__", ()):
            if isinstance(entry, EventRoleInfo):
                event_roles.append(entry)

    # Check the declared event role methods
    for attr_value in cls.__dict__.values():
        if isinstance(attr_value, EventRoleInfo):
            event_roles.append(attr_value)

    # Set combined collection of event roles for the given type
    setattr(cls, "__event_roles__", tuple(event_roles))


@dataclasses.dataclass
class EventRoleSearchState:
    """A saved state for backtracking when searching for roles to bind."""

    ctx: EventRoleBindingContext
    """The current context to pass to the binding function."""

    role_to_cast: EventRoleInfo
    """The current role being bound during this state."""

    binding_generator: Generator[Tuple[GameObject, ...], None, None]
    """The generator function providing the next set of results."""

    pending: Tuple[EventRoleInfo]
    """A queue of remaining event roles to bind."""


class RandomLifeEvent(LifeEvent, metaclass=RandomLifeEventMeta):
    """User-facing class for implementing behaviors around life events.

    Notes
    -----
    This is adapted from:
    https://github.com/ianhorswill/CitySimulator/blob/master/Assets/Codes/Action/Actions/ActionType.cs
    """

    __event_roles__: ClassVar[Tuple[EventRoleInfo]] = ()
    """Information about this events used for binding GameObjects."""

    def __init__(
        self,
        timestamp: SimDateTime,
        roles: Iterable[EventRole],
    ) -> None:
        """
        Parameters
        ----------
        timestamp
            Timestamp for when this event
        roles
            The names of roles mapped to GameObjects
        """
        super().__init__(timestamp, roles)

    def get_probability(self) -> float:
        """Get the probability of an instance of this event happening

        Returns
        -------
        float
            The probability of the event given the GameObjects bound
            to the roles in the LifeEventInstance
        """
        probability = 1.0
        contributor_count = 0

        for role in self.__event_roles__:
            if role.considerations:
                for gameobject in self.roles.get_all(role.name):
                    probability *= role.considerations.calculate_score(gameobject, self)
                    contributor_count += 1

        if contributor_count > 0:
            # Take the arithmetic mean of the contributing probability scores
            return probability ** (1 / contributor_count)
        else:
            return 0.5

    @abstractmethod
    def execute(self, world: World) -> None:
        """Executes the LifeEvent instance, emitting an event."""
        raise NotImplementedError

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Generator[RandomLifeEvent, None, None]:
        """Attempts to create a new LifeEvent instance

        Parameters
        ----------
        world
            Neighborly world instance
        bindings
            Suggested bindings of role names mapped to GameObjects

        Returns
        -------
        LifeEventInstance or None
            An instance of this life event if all roles are bound successfully
        """

        # Check if there are any roles that need to be bound
        if len(cls.__event_roles__) == 0:
            yield cls(world.get_resource(SimDateTime).copy(), EventRoleList())
            return

        # Stack of previous search states for when we fail to find a result
        history: list[EventRoleSearchState] = []

        # Starting context uses the given bindings
        ctx = EventRoleBindingContext(
            world=world, bindings=bindings if bindings else EventRoleList()
        )

        # Set up the initial state for binding
        current_state = EventRoleSearchState(
            ctx=ctx,
            role_to_cast=cls.__event_roles__[0],
            binding_generator=cls.__event_roles__[0].binding_fn(ctx),
            pending=cls.__event_roles__[1:],
        )

        while True:
            try:
                if len(current_state.pending) > 0:
                    # Find a single solution add this state to the stack and change the
                    # current state

                    new_bindings = EventRoleList(
                        [
                            *current_state.ctx.bindings,
                            *[
                                EventRole(current_state.role_to_cast.name, r)
                                for r in next(current_state.binding_generator)
                            ],
                        ]
                    )

                    # Add the current state to the history and keep iterating
                    history.append(current_state)

                    # Create a new context and state with the new bindings
                    new_ctx = EventRoleBindingContext(
                        world=world,
                        bindings=new_bindings,
                    )

                    current_state = EventRoleSearchState(
                        ctx=new_ctx,
                        role_to_cast=current_state.pending[0],
                        binding_generator=current_state.pending[0].binding_fn(new_ctx),
                        pending=current_state.pending[1:],
                    )
                else:
                    # This is the last role we need to bind.
                    # Exhaust all the solutions and return them as instances of the
                    # event
                    for results in current_state.binding_generator:
                        # Create combined list of bindings
                        new_bindings = EventRoleList(
                            [
                                *current_state.ctx.bindings,
                                *[
                                    EventRole(current_state.role_to_cast.name, r)
                                    for r in results
                                ],
                            ]
                        )

                        # yield an instance of the random event
                        yield cls(world.get_resource(SimDateTime).copy(), new_bindings)

                    # Check if there is any history to backtrack through.
                    # Return if not
                    if history:
                        current_state = history.pop()
                    else:
                        return

            except StopIteration:
                # We failed to find any more results. Pop the history stack and try
                # again. Or stop if we have not history
                if history:
                    current_state = history.pop()
                else:
                    return


class RandomLifeEventLibrary:
    """Class used to store LifeEvents that can be triggered randomly."""

    __slots__ = "_event_types"

    _event_types: OrderedSet[Type[RandomLifeEvent]]
    """Collection of RandomLifeEvent types used in the simulation."""

    def __init__(self) -> None:
        self._event_types = OrderedSet([])

    def add(self, life_event_type: Type[RandomLifeEvent]) -> None:
        """Register a new random LifeEvent type"""
        self._event_types.add(life_event_type)

    def pick_one(self, rng: random.Random) -> Type[RandomLifeEvent]:
        """
        Return a random registered random life event

        Parameters
        ----------
        rng
            A random number generator

        Returns
        -------
        Type[RandomLifeEvent]
            A randomly-chosen random event from the registry
        """
        return rng.choice(list(self._event_types))

    def __len__(self) -> int:
        """Get the number of registered random life events."""
        return len(self._event_types)


class EventHistory(Component, ISerializable):
    """Stores a record of all past events for a specific GameObject."""

    __slots__ = "_history"

    _history: List[LifeEvent]
    """A list of events in chronological-order."""

    def __init__(self) -> None:
        super().__init__()
        self._history = []

    def append(self, event: LifeEvent) -> None:
        """Record a new life event.

        Parameters
        ----------
        event
            The event to record.
        """
        self._history.append(event)

    def __iter__(self) -> Iterator[LifeEvent]:
        return self._history.__iter__()

    def to_dict(self) -> Dict[str, Any]:
        return {"events": [e.event_id for e in self._history]}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            [f"{type(e).__name__}({e.event_id})" for e in self._history],
        )


class EventLog(ISerializable):
    """Stores a record of all past life events."""

    __slots__ = "_history"

    _history: Dict[int, LifeEvent]
    """All recorded life events mapped to their event ID."""

    def __init__(self) -> None:
        super().__init__()
        self._history = {}

    def append(self, event: LifeEvent) -> None:
        """Record a new life event.

        Parameters
        ----------
        event
            The event to record.
        """
        self._history[event.event_id] = event

    def to_dict(self) -> Dict[str, Any]:
        return {str(key): entry.to_dict() for key, entry in self._history.items()}

    def __iter__(self) -> Iterator[LifeEvent]:
        return self._history.values().__iter__()

    def __getitem__(self, key: int) -> LifeEvent:
        return self._history[key]
