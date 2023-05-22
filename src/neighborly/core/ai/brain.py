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
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar, final

from neighborly.core.ai.behavior_tree import AbstractBTNode, BehaviorTree
from neighborly.core.ecs import Component, GameObject

_T = TypeVar("_T")


class WeightedList(Generic[_T]):
    """Manages a list of items mapped to weights to facilitate random selection."""

    __slots__ = "_items", "_weights", "_size", "_total_weight"

    def __init__(self) -> None:
        self._items: List[_T] = []
        self._weights: List[float] = []
        self._total_weight: float = 0.0
        self._size: int = 0

    def append(self, weight: float, item: _T) -> None:
        """Add an action to the list.

        Parameters
        ----------
        weight
            The weight associated with the action to add.
        item
            The item to add.
        """
        assert weight >= 0
        self._weights.append(weight)
        self._items.append(item)
        self._size += 1
        self._total_weight += weight

    def pick_one(self, rng: random.Random) -> _T:
        """Perform weighted random selection on the entries.

        Returns
        -------
        _T
            An action from the list.
        """
        return rng.choices(self._items, self._weights, k=1)[0]

    def above_thresh(self, threshold: float) -> WeightedList[_T]:
        """Filter list for all items with weights above a threshold.

        Parameters
        ----------
        threshold
            The weight threshold.

        Returns
        -------
        WeightedList[_T]
            A new list with the filtered values.
        """
        new_list: WeightedList[_T] = WeightedList()

        for i, weight in enumerate(self._weights):
            if weight >= threshold:
                new_list.append(weight, self._items[i])

        return new_list

    def has_options(self) -> bool:
        """Return True if there is at least one item with a positive weight."""
        return self._total_weight > 0

    def clear(self) -> None:
        """Remove all items from the list."""
        self._items.clear()
        self._weights.clear()
        self._size = 0
        self._total_weight = 0.0

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return bool(self._size)


class Consideration(Protocol):
    """Considerations are used to calculate the utility of goals and actions."""

    @abstractmethod
    def __call__(self, gameobject: GameObject) -> Optional[float]:
        """Perform utility score calculation for a GameObject.

        Parameters
        ----------
        gameobject
            A GameObject.

        Returns
        -------
        float or None
            A score from [0.0, 1.0].
        """
        raise NotImplementedError()


class ConsiderationList(List[Consideration]):
    """A collection of considerations associated with an action or goal."""

    def calculate_score(self, gameobject: GameObject) -> float:
        """Scores each consideration for a GameObject and returns the aggregate score.

        Parameters
        ----------
        gameobject
            A GameObject.

        Returns
        -------
        float
            The aggregate consideration score.
        """

        cumulative_score: float = 1.0
        consideration_count: int = 0

        for c in self:
            consideration_score = c(gameobject)
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


class ConsiderationDict(Dict[GameObject, ConsiderationList]):
    """Map of GameObjects to a collection of considerations."""

    def calculate_scores(self) -> Dict[GameObject, float]:
        """Scores all considerations relative to their mapped GameObject.

        Returns
        -------
        Dict[GameObject, float]
            The aggregate scores for each consideration list mapped to GameObjects.
        """
        scores: Dict[GameObject, float] = {}

        for gameobject, considerations in self.items():
            score = considerations.calculate_score(gameobject)
            scores[gameobject] = score

        return scores


class GoalNode(BehaviorTree):
    """Defines a goal and behavior tree to achieve that goal."""

    def __init__(self, root: Optional[AbstractBTNode] = None) -> None:
        super().__init__(root)
        self.blackboard["goal_stack"] = [self]

    @abstractmethod
    def is_complete(self) -> bool:
        """Return True if the goal is complete or invalid, False otherwise"""
        raise NotImplementedError

    @abstractmethod
    def get_utility(self) -> Dict[GameObject, float]:
        """Calculate how important and beneficial this goal is.

        Returns
        -------
        Dict[GameObject, float]
            GameObjects mapped to the utility they derive from the goal.
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
        """Get the stack of Goals and Sub-goals in this behavior"""
        return self.blackboard["goal_stack"]

    @abstractmethod
    def satisfied_goals(self) -> List[GoalNode]:
        """Get a list of goals that this goal satisfies."""
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
        """Perform weighted random selection on the entries.

        Returns
        -------
        GoalNode
            An action from the list.
        """
        return self._goals.pick_one(rng)

    def push_goal(self, priority: float, goal: GoalNode) -> None:
        """Add a goal to the collection.

        Parameters
        ----------
        priority
            How important is the goal on interval [0.0, 1.0].
        goal
            The goal node.
        """
        self._goals.append(priority, goal)

    def to_dict(self) -> Dict[str, Any]:
        return {}

    def has_options(self) -> bool:
        """Check if there are any goals with positive utilities.

        Returns
        -------
        bool
            True if there exists at least one goal with a weight
            greater than zero. False otherwise.
        """
        return self._goals.has_options()

    def clear_goals(self) -> None:
        """Clear the collection of goals."""
        self._goals.clear()

    def __len__(self) -> int:
        return len(self._goals)

    def __bool__(self) -> bool:
        return bool(self._goals)


class AIBrain(Component):
    """Marks a GameObject as being AI-controlled."""

    def __init__(self) -> None:
        super().__init__()

    def to_dict(self) -> Dict[str, Any]:
        return {}
