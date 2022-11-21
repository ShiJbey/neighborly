from __future__ import annotations

from typing import Callable, List, Set, Tuple, Union

from neighborly.core.ecs import Component, World
from neighborly.core.event import Event
from neighborly.core.life_event import EventProbabilityFn


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


class Action:
    def __init__(self, uid: int, rules: List[ActionRule], *roles: str) -> None:
        self.uid: int = uid
        self.rules: List[ActionRule] = rules

    def find_match(self, world: World) -> Tuple[Event, float]:
        raise NotImplementedError()

    def __eq__(self, other: Action) -> bool:
        return self.uid == other.uid

    def __hash__(self) -> int:
        return self.uid


class ActionRule:
    """
    ActionRules are combinations of patterns and probabilities for
    when an action is allowed to occur. A single action is mapped
    to one or more action rules.
    """

    def __init__(
        self,
        bind_fn: Callable[..., Event],
        probability: Union[EventProbabilityFn, float] = 1.0,
    ) -> None:
        self.bind_fn: Callable[..., Event] = bind_fn
        self.probability_fn: EventProbabilityFn = (
            probability if callable(probability) else (lambda world, event: probability)
        )
