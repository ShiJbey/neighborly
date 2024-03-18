"""Action Abstract Base Types.

"""

from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from typing import Any, Callable, Iterable, Optional, Protocol

import attrs
from repraxis import RePraxisDatabase
from repraxis.query import DBQuery

from neighborly.ecs import GameObject, World


class ActionConsideration:
    """Helps calculate scores for potential actions an agent might take.

    Parameters
    ----------
    tags
        Descriptive tags used to match this consideration with actions instances.
    value
        An static value to return as the consideration score if the
        preconditions pass. If value takes precedence over value_fn if both are given.
    value_fn
        A callable that calculates a consideration score given action instance.
    precondition_fn
        A callable that determines if the consideration applies.
    """

    def __init__(
        self,
        tags: Iterable[str],
        value: Optional[float] = None,
        value_fn: Optional[Callable[[ActionInstance], float]] = None,
        precondition_fn: Optional[Callable[[ActionInstance], bool]] = None,
        preconditions: Optional[list[str]] = None,
    ) -> None:
        pass


class ActionOnExecuteFn(Protocol):
    """Callback executed when an action executes."""

    def __call__(self, world: World, instance: ActionInstance) -> bool:
        """Called when an instance of this action executes.

        Parameters
        ----------
        bindings
            The bindings owned by the instance

        Returns
        -------
        bool
            True if the action succeeded, False otherwise.
        """

        raise NotImplementedError()


@attrs.define
class Action:
    """A definition for an action that can be performed by an agent."""

    action_id: str
    """A unique ID for this action type."""
    agent_type: str
    """The type of agent that can execute this action."""
    on_execute: ActionOnExecuteFn
    """Called when an instance of this action executes."""
    parameters: tuple[str, ...] = attrs.field(default=())
    """Variables to bind to variables given to the instantiate method."""
    description: str = ""
    """A templated description of the action."""
    preconditions: list[str] = attrs.field(factory=list)
    """RePraxis query statements."""
    tags: set[str] = attrs.field(factory=set)
    """Tags and keywords describing this action."""

    def create_instances(
        self, agent: GameObject, *params: object
    ) -> list[ActionInstance]:
        """Create eligible instances of this action.

        Parameters
        ----------
        agent
            The agent executing the action.
        bindings
            Additional bindings to pass to the preconditions.
        params:
            Additional items to bind to parameter names

        Returns
        -------
        list[ActionInstance]
            A list of the eligible action instances.
        """

        db = agent.world.resources.get_resource(RePraxisDatabase)

        query = DBQuery(self.preconditions)

        query_bindings: dict[str, object] = {"?agent": agent.uid}

        for i, obj in enumerate(params):
            if i < len(self.parameters):
                parameter_name = self.parameters[i]
                if isinstance(obj, GameObject):
                    query_bindings[f"?{parameter_name}"] = obj.uid
                else:
                    query_bindings[f"?{parameter_name}"] = obj

        results = query.run(db, [query_bindings])

        if results.success is False:
            return []

        action_instances: list[ActionInstance] = []

        for result in results.bindings:
            action_instances.append(
                ActionInstance(agent.world, action=self, bindings=result)
            )

        return action_instances


class ActionInstance:
    """An instantiation of an action."""

    __slots__ = ("world", "action", "bindings")

    world: World
    """The simulation's world instance."""
    roles: dict[str, GameObject]
    """Role names mapped to GameObjects."""
    action: Action
    """The action this is an instantiation of."""
    bindings: dict[str, object]
    """Bindings from the database query."""

    def __init__(
        self, world: World, action: Action, bindings: dict[str, object]
    ) -> None:
        self.world = world
        self.action = action
        self.bindings = bindings

    @property
    def description(self) -> str:
        """Description of this instance."""
        description = self.action.description

        # Replace [variable_name] with the string of the object in the bindings
        for k, v in self.bindings:
            description = description.replace(f"[{k[1:]}]", str(v))

        return description

    def execute(self, world: World) -> bool:
        """Execute the action.

        Parameters
        ----------
        world
            The simulations world instance.

        Returns
        -------
        bool
            True if the action succeeded, False otherwise.
        """
        return self.action.on_execute(world, self)


class ActionListener(Protocol):
    """A callable that executes an effect when an action is executed."""

    @abstractmethod
    def __call__(self, action: ActionInstance) -> None:
        """Execute the listener."""

        raise NotImplementedError()


class ActionCastingRule(Protocol):
    """A callable that tries to find adequate bindings for action instance variables."""

    @abstractmethod
    def __call__(self, agent: GameObject) -> list[dict[str, Any]]:
        """Cast variable bindings for an action instance.

        Parameters
        ----------
        agent
            The agent executing the action

        Returns
        -------
        list[dict[str, Any]]
            Potential variable bindings for the action instance.
        """

        raise NotImplementedError()


class ActionLibrary:
    """A repository of actions, listeners, and considerations."""

    __slots__ = ("actions", "listeners", "considerations")

    actions: dict[str, Action]
    """Action definitions indexed by action ID."""
    listeners: defaultdict[str, list[tuple[ActionListener, int]]]
    """Collections of actions listeners indexed by action ID."""
    considerations: defaultdict[str, list[ActionConsideration]]
    """Collections of considerations indexed by action ID."""

    def __init__(self) -> None:
        self.actions = {}
        self.listeners = defaultdict(list)
        self.considerations = defaultdict(list)


def add_action_definition(world: World, action: Action) -> None:
    """Add an action definition to the internal library.

    Parameters
    ----------
    world
        The simulation's world instance.
    action
        The action to add.
    """

    world.resources.get_resource(ActionLibrary).actions[action.action_id] = action


def add_action_consideration(
    world: World, action_id: str, consideration: ActionConsideration
) -> None:
    """Add a consideration that contributes to an action's utility score.

    Parameters
    ----------
    world
        The simulation's World instance.
    action_id
        The action this consideration is associated with.
    consideration
        The consideration to call.
    """

    world.resources.get_resource(ActionLibrary).considerations[action_id].append(
        consideration
    )


def remove_action_consideration(
    world: World,
    action_id: str,
    consideration: ActionConsideration,
) -> None:
    """Remove a consideration from an action.

    Parameters
    ----------
    world
        The simulation's world instance.
    action_id
        The ID of the action.
    consideration
        The consideration to remove.
    """

    world.resources.get_resource(ActionLibrary).considerations[action_id].remove(
        consideration
    )


def remove_all_action_considerations(world: World, action_id: str) -> None:
    """Remove all considerations from an action.

    Parameters
    ----------
    world
        The simulation's World instance.
    action_id
        The ID of the action.
    """

    del world.resources.get_resource(ActionLibrary).considerations[action_id]


def add_action_listener(
    world: World, action_id: str, listener: ActionListener, order: int = 0
) -> None:
    """Add an effect that triggers when an action is executed.

    Parameters
    ----------
    world
        The simulation's World instance.
    action_id
        The ID of the action this listener is called in response to.
    listener
        The callable to execute.
    order
        The listeners relative position within the listener priority queue. The higher
        the order, the later the lister is called.
    """

    world.resources.get_resource(ActionLibrary).listeners[action_id].append(
        (listener, order)
    )

    world.resources.get_resource(ActionLibrary).listeners[action_id].sort(
        key=lambda e: e[1]
    )


def remove_action_listener(
    world: World, action_id: str, listener: ActionListener
) -> None:
    """Remove a listener from an action.

    Parameters
    ----------
    world
        The simulation's World instance.
    action_id
        The ID of the action.
    listener
        The listener to remove.
    """
    listeners = world.resources.get_resource(ActionLibrary).listeners[action_id]

    world.resources.get_resource(ActionLibrary).listeners[action_id] = [
        (l, p) for l, p in listeners if l != listener
    ]


def remove_all_action_listeners(world: World, action_id: str) -> None:
    """Remove all listeners from an action.

    Parameters
    ----------
    world
        The simulation's World instance.
    action_id
        The ID of the action.
    """

    del world.resources.get_resource(ActionLibrary).listeners[action_id]


def add_action_casting_rule(
    world: World,
    action_id: str,
    rule: ActionCastingRule,
) -> None:
    """Add a precondition rule for how an action could be instantiated.

    Parameters
    ----------
    world
        The simulation's World instance.
    action_id
        The ID of the action.
    rule
        The rule to add.
    """

    raise NotImplementedError()


def remove_action_casting_rule(
    world: World,
    action_id: str,
    rule: ActionCastingRule,
) -> None:
    """Remove a precondition rule for how an action could be instantiated.

    Parameters
    ----------
    world
        The simulation's World instance.
    action_id
        The ID of the action.
    rule
        The rule to removed.
    """

    raise NotImplementedError()


def remove_all_action_casting_rules(world: World, action_id: str) -> None:
    """Remove all precondition rules for how an action could be instantiated.

    Parameters
    ----------
    world
        The simulation's World instance.
    action_id
        The ID of the action.
    """

    raise NotImplementedError()


def instantiate_action(
    action_id: str, agent: GameObject, bindings: Optional[dict[str, Any]] = None
) -> list[ActionInstance]:
    """Create instances of the given action.

    Parameters
    ----------
    action_id
        The ID of the action.
    agent
        The agent performing the action.
    bindings
        Optional variable bindings.
    """

    raise NotImplementedError()
