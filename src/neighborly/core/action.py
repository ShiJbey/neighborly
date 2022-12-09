from __future__ import annotations

from logging import getLogger
from typing import ClassVar, Dict, List, Optional, Protocol, Set

from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.event import Event, EventLog, RoleList
from neighborly.core.time import SimDateTime

logger = getLogger(__name__)


class RoleBinder(Protocol):
    """A function that finds GameObjects and binds them to EventRoles for an Action"""

    def __call__(
        self, world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[RoleList]:
        raise NotImplementedError


class ActionEffect(Protocol):
    """A callback function executed when an action is executed"""

    def __call__(self, world: World, event: Event) -> None:
        raise NotImplementedError


class ActionInstance:
    """
    Action information with a set of characters bound to specific roles

    Attributes
    ----------
    name: str
        The name of the action (used when registering action with ActionLibrary)
    roles: RoleList
        Function that binds GameObjects to roles associated with this Action
    effect_fn: Optional[ActionEffect]
        The effect function called when the action is triggered
    """

    __slots__ = "name", "roles", "effect_fn"

    def __init__(
        self,
        name: str,
        roles: RoleList,
        effect: Optional[ActionEffect],
    ) -> None:
        self.name: str = name
        self.roles: RoleList = roles
        self.effect_fn: Optional[ActionEffect] = effect

    def execute(self, world: World) -> None:
        """Executes the action instance, emitting an event"""
        event = Event(
            name=self.name,
            timestamp=world.get_resource(SimDateTime).to_iso_str(),
            roles=[r for r in self.roles],
        )

        world.get_resource(EventLog).record_event(event)

        if self.effect_fn is not None:
            self.effect_fn(world, event)


class Action:
    """
    Characters take actions with other characters at the same location.
    Actions have preconditions, effects, and resulting events.

    Attributes
    ----------
    name: str
        The name of the action (used when registering action with ActionLibrary)
    role_bind_fn: RoleBinder
        Function that binds GameObjects to roles associated with this Action
    effect_fn: ActionEffect
        The effect function called when the action is triggered
    """

    __slots__ = "name", "role_bind_fn", "effect_fn"

    def __init__(
        self,
        name: str,
        role_bind_fn: RoleBinder,
        effect: Optional[ActionEffect] = None,
    ) -> None:
        self.name: str = name
        self.role_bind_fn: RoleBinder = role_bind_fn
        self.effect_fn: Optional[ActionEffect] = effect

    def get_name(self) -> str:
        """Return the name of the Action"""
        return self.name

    def instantiate(
        self, world: World, *args: GameObject, **kwargs: GameObject
    ) -> Optional[ActionInstance]:
        """
        Create an instance of this action

        Parameters
        ----------
        world: World
            The World instance to bind GameObject from
        *args: GameObject
            Positional role bindings
        **args: GameObject
            Keyword role bindings
        """
        if roles := self.role_bind_fn(world, *args, **kwargs):
            return ActionInstance(name=self.name, roles=roles, effect=self.effect_fn)

        return None

    def try_execute_action(
        self, world: World, *args: GameObject, **kwargs: GameObject
    ) -> bool:
        """
        Attempt to instantiate and execute this Action

        Parameters
        ----------
        world: World
            Neighborly world instance
        *args: GameObject
            Positional role bindings
        **args: GameObject
            Keyword role bindings

        Returns
        -------
        bool
            Returns True if the action is successfully instantiated and executed
        """
        action_instance = self.instantiate(world, *args, **kwargs)
        if action_instance is not None:
            action_instance.execute(world)
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
        super(Component, self).__init__()
        self.actions: Set[Action] = set(actions)
