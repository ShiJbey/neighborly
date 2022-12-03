from __future__ import annotations

from logging import getLogger
from typing import Callable, ClassVar, Dict, List, Optional, Protocol, Set, Tuple

from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.event import Event, EventLog, EventRole, RoleList
from neighborly.core.query import Query, QueryFilterFn
from neighborly.core.time import SimDateTime

logger = getLogger(__name__)


class RoleBinder(Protocol):
    """Callback function called when an action is executed"""

    def __call__(self, world: World) -> Optional[RoleList]:
        raise NotImplementedError


class ActionEffect(Protocol):
    """Callback function called when an action is executed"""

    def __call__(self, world: World, event: Event) -> None:
        raise NotImplementedError


class ActionConsideration(Protocol):
    """Function called to determine a characters propensity for an action"""

    def __call__(self, world: World, gameobject: GameObject) -> int:
        raise NotImplementedError


class ActionRole:
    def __init__(self, name: str, precondition: Optional[QueryFilterFn]) -> None:
        self.name: str = name
        self.precondition: QueryFilterFn = precondition if precondition else (lambda w, *g: True)


def bind_action_roles(initiator: ActionRole, *other_roles: ActionRole) -> RoleBinder:
    # Determine the names of roles
    role_vars: List[str] = [initiator.name]
    role_vars.extend([role.name for role in other_roles])

    def bind_fn(world: World) -> RoleList:
        Query(find=tuple(role_vars), clauses=[])

    return bind_fn


class Action:
    """
    Characters take actions with other characters at the same location.
    Actions have preconditions, effects, and resulting events.

    Attributes
    ----------
    name: str
        The name of the action (used when registering action with ActionLibrary)
    initiator_role: ActionRole
        The associated role for the initiator of the action
    other_roles: Tuple[ActionRole,...]
        Additional roles associated with this action
    effect_fn: ActionEffect
        The effect function called when the action is triggered
    """

    __slots__ = "name", "role_bind_fn", "effect_fn"

    def __init__(
        self,
        name: str,
        role_bind_fn: Callable[[World], Optional[RoleList]],
        effect: Optional[ActionEffect] = None,
    ) -> None:
        self.name: str = name
        self.role_bind_fn: Callable[[World], RoleList] = role_bind_fn
        self.effect_fn: ActionEffect = effect if effect is not None else (lambda world, event: None)

    def get_name(self) -> str:
        """Return the name of the Action"""
        return self.name

    @staticmethod
    def _bind_roles(query: Query, *args: GameObject, **kwargs: GameObject):
        """Searches the ECS for a game object that meets the given conditions"""

        if args and kwargs:
            raise RuntimeError("Only positional bindings or named bindings may be used. Not both.")

        bindings: Dict[str, int] = {}
        if args:
            bindings = {query.get_symbols()[i]: gameobject.id for i, gameobject in enumerate(args)}

        if kwargs:
            bindings = {role_name: gameobject.id for role_name, gameobject in kwargs.items()}

        def wrapped(world: World) -> Optional[RoleList]:
            result_set = query.execute(world, **bindings)

            if len(result_set):
                chosen_result: Tuple[int, ...] = world.get_resource(NeighborlyEngine).rng.choice(result_set)
                return RoleList(
                    [EventRole(name, gameobject.id) for name, gameobject in zip(query.get_symbols(), chosen_result)]
                )

            return None

        return wrapped

    def instantiate(self, world: World, *args: GameObject, **kwargs: GameObject) -> Optional[Event]:
        """Create an event instance using the pattern"""
        if roles := self._bind_roles_fn(world, *args, **kwargs):
            return Event(
                name=self.name,
                timestamp=world.get_resource(SimDateTime).to_iso_str(),
                roles=[EventRole(n, gid) for n, gid in roles.items()],
            )

        return None

    def execute(self, world: World, event: Event) -> None:
        """Run the effects function using the given event"""
        world.get_resource(EventLog).record_event(event)
        self.effect_fn(world, event)

    def try_execute_event(self, world: World, **bindings: GameObject) -> bool:
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
        if event is not None:
            self.execute(world, event)
            return True
        return False


class ActionLibrary:
    """
    Static class used to store instances of LifeEventTypes for
    use at runtime.
    """

    _registry: ClassVar[Dict[str, Action]] = {}

    @classmethod
    def add(cls, action: Action, name: Optional[str] = None) -> None:
        """Register a new Action mapped to a name"""
        key_name = name if name else action.get_name()
        if key_name in cls._registry:
            logger.debug(f"Overwriting Action: ({key_name})")
        cls._registry[key_name] = action

    @classmethod
    def get_all(cls) -> List[Action]:
        """Get all Actions stored in the Library"""
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> Action:
        """Get an Action using a name"""
        return cls._registry[name]


class AvailableActions(Component):
    """
    Tracks all the Actions that are available at a given location

    Attributes
    ----------
    actions: Set[Action]
        The actions that characters can take
    """

    __slots__ = "actions"

    def __init__(self, actions: List[Action]) -> None:
        super().__init__()
        self.actions: Set[Action] = set(actions)
