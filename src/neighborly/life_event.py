from __future__ import annotations

import random
from abc import ABC, ABCMeta, abstractmethod
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
)

import attrs
from ordered_set import OrderedSet

from neighborly.ecs import Component, Event, GameObject, ISerializable, World
from neighborly.stats import Stat, StatModifier
from neighborly.time import SimDateTime


class EventRole:
    """A role within a random life event that a GameObject is bound to."""

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
        return f"{type(self).__name__}({self.name}: {self.gameobject.name})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name}: {self.gameobject.name})"


class EventRoleList:
    """A collection of event roles."""

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
            The roles to instantiate the list with, by default None
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

    __slots__ = "_timestamp"

    _timestamp: SimDateTime
    """The date when this event occurred."""

    def __init__(
        self,
        world: World,
        timestamp: SimDateTime,
    ) -> None:
        """
        Parameters
        ----------
        world
            The world instance
        timestamp
            The timestamp for when this event
        """
        super().__init__(world)
        self._timestamp = timestamp.copy()

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            **super().to_dict(),
            "timestamp": str(self._timestamp),
        }

    def __repr__(self) -> str:
        return "{}(id={}, timestamp={})".format(
            type(self).__name__, self.event_id, str(self.timestamp)
        )

    def __str__(self) -> str:
        return "{} [@ {}]".format(
            type(self).__name__,
            str(self.timestamp),
        )


@attrs.define()
class EventBindingContext:
    """Manages information related to the current state of cast roles."""

    world: World
    """The world instance that the GameObjects in the role list belong to."""

    bindings: EventRoleList = attrs.field(factory=EventRoleList)
    """The current set of casted roles."""

    data: Dict[str, Any] = attrs.field(factory=dict)
    """Additional event data that are not GameObject roles."""


EventRoleBindingGeneratorFn = Callable[
    [EventBindingContext], Generator[Tuple[GameObject, ...], None, None]
]
"""Role casting functions yield GameObjects to bind to a role."""

_T = TypeVar("_T", bound="RandomLifeEvent", contravariant=True)


class EventConsideration(Protocol[_T]):
    """Probability modifier for random life events."""

    def __call__(self, event: _T) -> Optional[StatModifier]:
        raise NotImplementedError()


@attrs.define
class _EventRoleWrapper:
    """Information about an event role.

    These are created when the @event_role decorator is used within a random life event
    class definition. It defines the name of the role, a generator that produces
    potential bindings, and considerations for GameObjects that are bound to the role.
    """

    name: str
    """The name of the role."""

    binding_fn: EventRoleBindingGeneratorFn
    """The function used to bind GameObject instances to the role."""

    def __call__(
        self, ctx: EventBindingContext
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        return self.binding_fn(ctx)


@attrs.define
class _EventConsiderationWrapper(EventConsideration[_T]):
    """Wraps an event consideration function for use in metaclass construction."""

    fn: EventConsideration[_T]

    def __call__(self, event: _T) -> Optional[StatModifier]:
        return self.fn(event)


def event_role(name: str):
    """A decorator to indicate that a function is for casting a role."""

    def event_role_decorator(fn: EventRoleBindingGeneratorFn):
        return _EventRoleWrapper(name, fn)

    return event_role_decorator


def event_consideration():
    """A decorator to indicate that a static method is an event consideration."""

    def decorator(fn: EventConsideration):
        return _EventConsiderationWrapper(fn)

    return decorator


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
        RandomLifeEventMeta._detect_roles(cls)
        RandomLifeEventMeta._detect_considerations(cls)
        return cls

    @staticmethod
    def _detect_roles(cls: type) -> None:
        """Detect static methods that use the event_role decorator

        Parameters
        ----------
        cls
            The class to process
        """
        event_roles: List[_EventRoleWrapper] = []

        # Check the existing event role methods of the parents
        for base_class in cls.__bases__:
            for entry in getattr(base_class, "__event_roles__", ()):
                if isinstance(entry, _EventRoleWrapper):
                    event_roles.append(entry)

        # Check the declared event role methods
        for attr_name, attr_value in cls.__dict__.items():
            if type(attr_value) == staticmethod:
                attr = getattr(cls, attr_name)
                if isinstance(attr, _EventRoleWrapper):
                    event_roles.append(attr)

        # Set combined collection of event roles for the given type
        setattr(cls, "__event_roles__", tuple(event_roles))

    @staticmethod
    def _detect_considerations(cls: type) -> None:
        """Detect static methods that use the event_consideration decorator.

        Parameters
        ----------
        cls
            The class to process
        """
        probability_modifiers: List[_EventConsiderationWrapper] = []

        # Check the existing probability modifiers in base classes
        for base_class in cls.__bases__:
            for entry in getattr(base_class, "probability_modifiers", []):
                if isinstance(entry, _EventConsiderationWrapper):
                    probability_modifiers.append(entry)

        # Check the declared probability modifiers
        for attr_name, attr_value in cls.__dict__.items():
            if type(attr_value) == staticmethod:
                attr = getattr(cls, attr_name)
                if isinstance(attr, _EventConsiderationWrapper):
                    probability_modifiers.append(attr)

        # Set combined collection of event roles for the given type
        setattr(cls, "probability_modifiers", tuple(probability_modifiers))


@attrs.define
class EventRoleSearchState:
    """A saved state for backtracking when searching for roles to bind."""

    ctx: EventBindingContext
    """The current context to pass to the binding function."""

    role_to_cast: _EventRoleWrapper
    """The current role being bound during this state."""

    binding_generator: Generator[Tuple[GameObject, ...], None, None]
    """The generator function providing the next set of results."""

    pending: Tuple[_EventRoleWrapper, ...]
    """A queue of remaining event roles to bind."""


class RandomLifeEvent(LifeEvent, metaclass=RandomLifeEventMeta):
    """User-facing class for implementing behaviors around life events.

    Notes
    -----
    This is adapted from:
    https://github.com/ianhorswill/CitySimulator/blob/master/Assets/Codes/Action/Actions/ActionType.cs
    """

    __event_roles__: ClassVar[Tuple[_EventRoleWrapper, ...]] = ()
    """Information about this events used for binding GameObjects."""

    base_probability: ClassVar[float] = 0.5
    """The base probability that this event will occur."""

    probability_modifiers: ClassVar[List[EventConsideration]] = []
    """Functions that return modifiers for the base probability."""

    __slots__ = "_roles"

    _roles: EventRoleList
    """The bound roles of this life event."""

    def __init__(
        self,
        world: World,
        timestamp: SimDateTime,
        roles: Iterable[EventRole],
        **kwargs: Any,
    ) -> None:
        """
        Parameters
        ----------
        timestamp
            The timestamp for when this event occurred
        roles
            The names of roles mapped to GameObjects
        """
        super().__init__(world, timestamp)
        self._roles: EventRoleList = EventRoleList(roles)

    @property
    def roles(self) -> EventRoleList:
        return self._roles

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            **super().to_dict(),
            "roles": [role.to_dict() for role in self._roles],
        }

    def __getitem__(self, role_name: str) -> GameObject:
        return self._roles.get_first(role_name)

    def __repr__(self) -> str:
        return "{}(id={}, timestamp={}, roles=[{}])".format(
            type(self).__name__, self.event_id, str(self.timestamp), self._roles
        )

    def __str__(self) -> str:
        return "{} [@ {}] {}".format(
            type(self).__name__,
            str(self.timestamp),
            ", ".join([str(role) for role in self._roles]),
        )

    def get_probability(self) -> float:
        """Get the probability of an instance of this event happening

        Returns
        -------
        float
            The probability of the event given the GameObjects bound
            to the roles in the LifeEventInstance
        """
        incidence_probability = Stat(base_value=type(self).base_probability)

        for modifier_fn in type(self).probability_modifiers:
            if modifier := modifier_fn(self):
                incidence_probability.add_modifier(modifier)

        return incidence_probability.value

    def dispatch(self) -> None:
        self.execute()
        super().dispatch()

    def on_dispatch(self) -> None:
        self.execute()

    @abstractmethod
    def execute(self) -> None:
        """Executes the LifeEvent instance, emitting an event."""
        raise NotImplementedError

    @classmethod
    def _generate_role_bindings(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Generator[EventBindingContext, None, None]:
        """Attempts to generate multiple valid Event role lists for this event

        Parameters
        ----------
        world
            Neighborly world instance
        bindings
            Suggested bindings of role names mapped to GameObjects

        Returns
        -------
        Generator[EventBindingContext, None, None]
            An generator function that produces instance of this life event
        """

        # Check if there are any roles that need to be bound
        if len(cls.__event_roles__) == 0:
            yield EventBindingContext(world=world)
            return

        # Stack of previous search states for when we fail to find a result
        history: list[EventRoleSearchState] = []

        # Starting context uses the given bindings
        ctx = EventBindingContext(
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

                    new_bound_roles: List[EventRole] = []

                    result = next(current_state.binding_generator)

                    if isinstance(result, tuple):
                        for gameobject in result:
                            new_bound_roles.append(
                                EventRole(
                                    current_state.role_to_cast.name, gameobject
                                )
                            )

                    elif isinstance(result, GameObject):
                        new_bound_roles.append(
                            EventRole(
                                current_state.role_to_cast.name, result
                            )
                        )

                    else:
                        raise TypeError(
                            "Expected GameObject or tuple but was: {}".format(
                                type(result)
                            )
                        )

                    new_bindings = EventRoleList(
                        [
                            *current_state.ctx.bindings,
                            *new_bound_roles,
                        ]
                    )

                    # Add the current state to the history and keep iterating
                    history.append(current_state)

                    # Create a new context and state with the new bindings
                    new_ctx = EventBindingContext(
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
                    for result in current_state.binding_generator:
                        new_bound_roles: List[EventRole] = []

                        if isinstance(result, tuple):
                            for gameobject in result:
                                new_bound_roles.append(
                                    EventRole(
                                        current_state.role_to_cast.name, gameobject
                                    )
                                )

                        elif isinstance(result, GameObject):
                            new_bound_roles.append(
                                EventRole(
                                    current_state.role_to_cast.name, result
                                )
                            )

                        else:
                            raise TypeError(
                                "Expected GameObject or tuple but was: {}".format(
                                    type(result)
                                )
                            )

                        new_bindings = EventRoleList(
                            [
                                *current_state.ctx.bindings,
                                *new_bound_roles,
                            ]
                        )

                        # yield an instance of the random event
                        yield EventBindingContext(
                            world=world,
                            bindings=new_bindings,
                            data=current_state.ctx.data.copy(),
                        )

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

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Optional[RandomLifeEvent]:
        """Attempts to create a new LifeEvent instance

        Parameters
        ----------
        world
            Neighborly world instance
        bindings
            Suggested bindings of role names mapped to GameObjects

        Returns
        -------
        RandomLifeEvent or None
            An instance of this life event if all roles are bound successfully
        """

        try:
            bindings = next(cls._generate_role_bindings(world, bindings))
            return cls(
                world=world,
                timestamp=world.resource_manager.get_resource(SimDateTime).copy(),
                roles=bindings.bindings,
                **bindings.data,
            )
        except StopIteration:
            return None

    @classmethod
    def generate(
        cls,
        world: World,
        bindings: Optional[EventRoleList] = None,
    ) -> Generator[RandomLifeEvent, None, None]:
        """Attempts to generate multiple valid instances of the life event class

        Parameters
        ----------
        world
            Neighborly world instance
        bindings
            Suggested bindings of role names mapped to GameObjects

        Returns
        -------
        Generator[RandomLifeEvent, None, None]
            An generator function that produces instance of this life event
        """
        for bindings in cls._generate_role_bindings(world, bindings):
            yield cls(
                world=world,
                timestamp=world.resource_manager.get_resource(SimDateTime).copy(),
                roles=bindings.bindings,
                **bindings.data,
            )


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

    _history: List[Event]
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

    def __iter__(self) -> Iterator[Event]:
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

    _history: Dict[int, Event]
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

    def __iter__(self) -> Iterator[Event]:
        return self._history.values().__iter__()

    def __getitem__(self, key: int) -> Event:
        return self._history[key]
