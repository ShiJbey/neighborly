from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union

from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.event import Event, EventLog, EventRole, RoleList
from neighborly.core.query import Query
from neighborly.core.settlement import Settlement
from neighborly.core.system import System
from neighborly.core.time import SimDateTime, TimeDelta

logger = logging.getLogger(__name__)


class RoleBinder(Protocol):
    """Function used to fill a RoleList"""

    def __call__(
        self, world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[RoleList]:
        raise NotImplementedError


class ILifeEvent(Protocol):
    """Interface for classes that create life events"""

    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def instantiate(
        self, world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[LifeEventInstance]:
        """Attempts to create a new Event instance"""
        raise NotImplementedError

    @abstractmethod
    def try_execute_event(
        self, world: World, *args: GameObject, **kwargs: GameObject
    ) -> bool:
        """Attempts to instantiate and execute the event"""
        raise NotImplementedError


class LifeEventRoleType:
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


class LifeEventInstance:
    """
    An instance of a life event with GameObjects bound to roles

    Attributes
    ----------
    name: str
        Name of the LifeEventType and the LifeEvent it instantiates
    roles: RoleList
        The roles that need to be cast for this event to be executed
    effect: EventEffectFn
        Function that executes changes to the world state base don the event
    """

    __slots__ = "name", "roles", "effect_fn"

    def __init__(
        self,
        name: str,
        roles: RoleList,
        effect: Optional[EventEffectFn],
    ) -> None:
        self.name: str = name
        self.roles: RoleList = roles
        self.effect_fn: Optional[EventEffectFn] = effect

    def execute(self, world: World) -> None:
        """Executes the LifeEvent instance, emitting an event"""
        event = Event(
            name=self.name,
            timestamp=world.get_resource(SimDateTime).to_iso_str(),
            roles=[r for r in self.roles],
        )

        world.get_resource(EventLog).record_event(event)

        if self.effect_fn is not None:
            self.effect_fn(world, event)


class LifeEvent:
    """
    User-facing class for implementing behaviors around life events

    This is adapted from:
    https://github.com/ianhorswill/CitySimulator/blob/master/Assets/Codes/Action/Actions/ActionType.cs

    Attributes
    ----------
    name: str
        Name of the LifeEventType and the LifeEvent it instantiates
    bind_fn: RoleBinder
        Function that attempt to bind roles for the LifeEvent
    probability: EventProbabilityFn
        The relative frequency of this event compared to other events
    effect: EventEffectFn
        Function that executes changes to the world state base don the event
    """

    __slots__ = "name", "probability", "bind_fn", "effect"

    def __init__(
        self,
        name: str,
        bind_fn: RoleBinder,
        probability: Union[EventProbabilityFn, float],
        effect: Optional[EventEffectFn] = None,
    ) -> None:
        self.name: str = name
        self.bind_fn: RoleBinder = bind_fn
        self.probability: EventProbabilityFn = (
            probability if callable(probability) else (lambda world, event: probability)
        )
        self.effect: Optional[EventEffectFn] = effect

    def get_name(self) -> str:
        return self.name

    def instantiate(
        self, world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[LifeEventInstance]:
        """
        Attempts to create a new LifeEvent instance

        Parameters
        ----------
        world: World
            Neighborly world instance
        **bindings: Dict[str, GameObject]
            Attempted bindings of GameObjects to RoleTypes
        """
        if roles := self.bind_fn(world, *args, **kwargs):
            return LifeEventInstance(self.name, roles, self.effect)
        return None

    def try_execute_event(
        self, world: World, *args: GameObject, **bindings: GameObject
    ) -> bool:
        """
        Attempt to instantiate and execute this LifeEventType

        Parameters
        ----------
        world: World
            Neighborly world instance
        **bindings: Dict[str, GameObject]
            Attempted bindings of GameObjects to RoleTypes

        Returns
        -------
        bool
            Returns True if the event is instantiated successfully and executed
        """
        event = self.instantiate(world, **bindings)
        rng = world.get_resource(NeighborlyEngine).rng
        if event is not None and rng.random() < self.probability(world, event):
            event.execute(world)
            return True
        return False


class LifeEvents:
    """
    Static class used to store instances of LifeEventTypes for
    use at runtime.
    """

    _registry: Dict[str, ILifeEvent] = {}

    @classmethod
    def add(cls, life_event: ILifeEvent, name: Optional[str] = None) -> None:
        """Register a new LifeEventType mapped to a name"""
        key_name = name if name else life_event.get_name()
        if key_name in cls._registry:
            logger.debug(f"Overwriting LifeEventType: ({key_name})")
        cls._registry[key_name] = life_event

    @classmethod
    def get_all(cls) -> List[ILifeEvent]:
        """Get all LifeEventTypes stores in the Library"""
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> ILifeEvent:
        """Get a LifeEventType using a name"""
        return cls._registry[name]


class LifeEventSystem(System):
    """
    LifeEventSimulator handles firing LifeEvents for characters
    and performing entity behaviors
    """

    def __init__(self, interval: Optional[TimeDelta] = None) -> None:
        super().__init__(interval=interval)

    def run(self, *args: Any, **kwarg: Any) -> None:
        """Simulate LifeEvents for characters"""
        settlement = self.world.get_resource(Settlement)
        rng = self.world.get_resource(NeighborlyEngine).rng

        # Perform number of events equal to 10% of the population

        for life_event in rng.choices(
            LifeEvents.get_all(), k=(int(settlement.population / 2))
        ):
            success = life_event.try_execute_event(self.world)
            if success:
                self.world.clear_command_queue()


class EventEffectFn(Protocol):
    """Callback function called when an event is executed"""

    def __call__(self, world: World, event: Event) -> None:
        raise NotImplementedError


class EventProbabilityFn(Protocol):
    """Function called to determine the probability of an event executing"""

    def __call__(self, world: World, event: LifeEventInstance) -> float:
        raise NotImplementedError


class RoleTypeBindFn(Protocol):
    """Callable that returns a GameObject that meets requirements for a given Role"""

    def __call__(
        self, world: World, roles: RoleList, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        raise NotImplementedError


def from_roles(*role_types: LifeEventRoleType) -> RoleBinder:
    """Binds roles using a list of LifeEventRoleTypes"""

    def binder_fn(
        world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[RoleList]:
        roles = RoleList()

        for role_type in role_types:
            filled_role = role_type.fill_role(
                world, roles, candidate=kwargs.get(role_type.name)
            )
            if filled_role is not None:
                role_list.add_role(filled_role)  # type: ignore
            else:
                # Return None if there are no available entities to fill
                # the current role
                return None

        return roles

    return binder_fn


def from_pattern(query: Query) -> RoleBinder:
    """Binds roles using a query pattern"""

    def binder_fn(
        world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[RoleList]:
        result_set = query.execute(
            world,
            **{role_name: gameobject.id for role_name, gameobject in kwargs.items()},
        )

        if len(result_set):
            chosen_result: Tuple[int, ...] = world.get_resource(
                NeighborlyEngine
            ).rng.choice(result_set)

            return RoleList(
                [
                    EventRole(role, gid)
                    for role, gid in dict(
                        zip(query.get_symbols(), chosen_result)
                    ).items()
                ]
            )

        return None

    return binder_fn
