"""
This module contains interfaces, components, and systems
related to character decision-making. Users of this library
should use these classes to override character decision-making
processes

This code is adapted from Brian Bucklew's IRDC talk on the AI in Caves of Qud and
Sproggiwood: 

https://www.youtube.com/watch?v=4uxN5GqXcaA&t=339s&ab_channel=InternationalRoguelikeDeveloperConference
"""
from __future__ import annotations

import random
from abc import abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, final

from neighborly.core.ai.behavior_tree import AbstractBTNode, BehaviorTree
from neighborly.core.ecs import Component, GameObject

_T = TypeVar("_T")


class WeightedList(Generic[_T]):
    """Manages a list of actions mapped to weights to facilitate random selection"""

    __slots__ = "_items", "_weights", "_size"

    def __init__(self) -> None:
        self._items: List[_T] = []
        self._weights: List[float] = []
        self._size: int = 0

    def append(self, weight: float, item: _T) -> None:
        """
        Add an action to the list

        Parameters
        ----------
        weight: int
            The weight associated with the action to add
        item: _T
            The item to add
        """
        self._weights.append(weight)
        self._items.append(item)
        self._size += 1

    def pick_one(self, rng: random.Random) -> _T:
        """Perform weighted random selection on the entries

        Returns
        -------
        _T
            An action from the list
        """
        return rng.choices(self._items, self._weights, k=1)[0]

    def clear(self) -> None:
        self._items.clear()
        self._weights.clear()
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return bool(self._size)


class GoalNode(BehaviorTree):
    """Defines a goal and behavior to achieve that goal including sub-goals"""

    __slots__ = "original_goal"

    def __init__(self, root: Optional[AbstractBTNode] = None) -> None:
        super().__init__(root)
        self.original_goal: Optional[GoalNode] = None
        self.blackboard["goal_stack"] = [self]

    @abstractmethod
    def get_utility(self) -> Dict[GameObject, float]:
        """
        Calculate how important and beneficial this goal is

        Returns
        -------
        Dict[GameObject, float]
            GameObjects mapped to the utility they derive from the goal
        """
        raise NotImplementedError

    @final
    def set_blackboard(self, blackboard: Dict[str, Any]) -> None:
        super().set_blackboard(blackboard)
        if "goal_stack" in self.blackboard:
            self.blackboard["goal_stack"].append(self)
        else:
            self.blackboard["goal_stack"] = [self]

    @final
    def take_action(self) -> None:
        """Perform an action in-service of this goal"""
        self.evaluate()

    @final
    def get_goal_stack(self) -> List[GoalNode]:
        stack: List[GoalNode] = [self]

        if self.original_goal:
            stack.extend(self.original_goal.get_goal_stack())

        return stack

    @abstractmethod
    def satisfied_goals(self) -> List[GoalNode]:
        """Get a list of goals that this goal satisfies"""
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, __o: object) -> bool:
        raise NotImplementedError()


class Goals(Component):
    """Tracks the GameObject's current goals that drive behavior"""

    __slots__ = "_goals"

    def __init__(self) -> None:
        super().__init__()
        self._goals: WeightedList[GoalNode] = WeightedList()

    def pick_one(self, rng: random.Random) -> GoalNode:
        """Perform weighted random selection on the entries

        Returns
        -------
        GoalNode
            An action from the list
        """
        return self._goals.pick_one(rng)

    def push_goal(self, priority: float, goal: GoalNode) -> None:
        """Add a goal to the AI"""
        self._goals.append(priority, goal)

    def to_dict(self) -> Dict[str, Any]:
        return {}

    def clear_goals(self) -> None:
        self._goals.clear()

    def __len__(self) -> int:
        return len(self._goals)

    def __bool__(self) -> bool:
        return bool(self._goals)


class AIBrain(Component):
    """Marks a GameObject as being AI-controlled"""

    def __init__(self) -> None:
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {}
