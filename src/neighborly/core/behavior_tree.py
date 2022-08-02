from abc import abstractmethod
from typing import Protocol

from neighborly.core.ecs import World
from neighborly.core.life_event import LifeEvent


class BehaviorNode(Protocol):
    """A single node in the behavior tree"""

    @abstractmethod
    def __call__(self, world: World, event: LifeEvent, **kwargs) -> bool:
        """Evaluate the behavior tree node"""
        raise NotImplemented


def invert(node: BehaviorNode) -> BehaviorNode:
    """
    Returns precondition function that checks if the
    current year is less than the given year
    """

    def fn(world: World, event: LifeEvent, **kwargs) -> bool:
        return not node(world, event, **kwargs)

    return fn


def selector(*nodes: BehaviorNode) -> BehaviorNode:
    """
    Returns precondition function that checks if the
    current year is less than the given year
    """

    def fn(world: World, event: LifeEvent, **kwargs) -> bool:
        for node in nodes:
            res = node(world, event, **kwargs)
            if res is True:
                return True
        return False

    return fn


def sequence(*nodes: BehaviorNode) -> BehaviorNode:
    """
    Returns precondition function that checks if the
    current year is less than the given year
    """

    def fn(world: World, event: LifeEvent, **kwargs) -> bool:
        for node in nodes:
            res = node(world, event, **kwargs)
            if res is False:
                return False
        return True

    return fn
