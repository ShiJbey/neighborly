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
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional

from neighborly.core.ecs import Component


class Action(ABC):
    """Actions are operations performed by GameObjects to change the simulation"""

    @abstractmethod
    def execute(self) -> bool:
        """
        Attempt to perform the action

        Returns
        -------
        bool
            Return True if the action was successful, False otherwise
        """
        raise NotImplementedError()


class WeightedActionList:
    """Manages a list of actions mapped to weights to facilitate random selection"""

    __slots__ = "_actions", "_weights", "_size", "_rng"

    def __init__(self, rng: random.Random) -> None:
        self._actions: List[Action] = []
        self._weights: List[int] = []
        self._size: int = 0
        self._rng: random.Random = rng

    def append(self, weight: int, action: Action) -> None:
        """
        Add an action to the list

        Parameters
        ----------
        weight: int
            The weight associated with the action to add
        action: Action
            The action
        """
        self._weights.append(weight)
        self._actions.append(action)
        self._size += 1

    def pick_one(self) -> Action:
        """Perform weighted random selection on the entries

        Returns
        -------
        Action
            An action from the list
        """
        return self._rng.choices(self._actions, self._weights, k=1)[0]

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return bool(self._size)


class Goal(ABC):
    """Goals drive what it is that a character wants to do"""

    __slots__ = "original_intent"

    def __init__(self, original_intent: Optional[Goal] = None) -> None:
        super().__init__()
        self.original_intent: Optional[Goal] = original_intent

    @abstractmethod
    def is_complete(self) -> bool:
        """Check if the goal is satisfied

        Returns
        -------
        bool
            True if the goal is satisfied, False otherwise
        """
        raise NotImplementedError()

    @abstractmethod
    def take_action(self, goal_stack: GoalStack) -> None:
        """Perform an action in-service of this goal"""
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the goal to a dictionary"""
        raise NotImplementedError()


class GoalStack:
    """A set of goals that all share the same base goal"""

    __slots__ = "_goals"

    def __init__(self, goals: Optional[Iterable[Goal]] = None) -> None:
        super().__init__()
        self._goals: List[Goal] = list(goals) if goals else []

    def remove_completed(self) -> None:
        """Remove completed goals from the top of the stack"""
        while len(self) and self.peek().is_complete():
            self.pop()

    def take_action(self) -> None:
        """Perform an action in-service of this goal"""
        if len(self):
            self.peek().take_action(self)

    def push(self, goal: Goal) -> None:
        """Add a goal to the top of the stack"""
        self._goals.append(goal)

    def pop(self) -> Goal:
        """Remove the goal at the top of the stack"""
        return self._goals.pop()

    def peek(self) -> Goal:
        """Returns the Goal at the top of the stack without removing it"""
        return self._goals[-1]

    def to_dict(self) -> Dict[str, Any]:
        return {"goals": [g.to_dict() for g in self._goals]}

    def __len__(self) -> int:
        return len(self._goals)

    def __bool__(self) -> bool:
        return bool(self._goals)


class WeightedGoalStackList:
    """Manages a list of actions mapped to weights to facilitate random selection"""

    __slots__ = "_goals", "_weights", "_size", "_rng"

    def __init__(self, rng: random.Random) -> None:
        self._goals: List[GoalStack] = []
        self._weights: List[int] = []
        self._size: int = 0
        self._rng: random.Random = rng

    def append(self, weight: int, stack: GoalStack) -> None:
        """
        Add an action to the list

        Parameters
        ----------
        weight: int
            The weight associated with the action to add
        stack: GoalStack
            The stack of goals
        """
        self._weights.append(weight)
        self._goals.append(stack)
        self._size += 1

    def pick_one(self) -> GoalStack:
        """Perform weighted random selection on the entries

        Returns
        -------
        Action
            An action from the list
        """
        return self._rng.choices(self._goals, self._weights, k=1)[0]

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return bool(self._size)


class AIComponent(Component):
    """
    The AI component is responsible for driving agent behavior by tracking goals that
    in-turn execute actions and create new goals.
    """

    __slots__ = "_goals"

    def __init__(self, rng: random.Random) -> None:
        super().__init__()
        # Here we use _goals as a stack. Perhaps in a later update this could change
        # to something like a priority queue
        self._goals: WeightedGoalStackList = WeightedGoalStackList(rng)

    def take_action(self) -> None:
        """
        Get the next action for this character

        Parameters
        ----------
        world: World
            The world instance the character belongs to
        gameobject: GameObject
            The GameObject instance this module is associated with
        """

        if not self._goals:
            return

        chosen_goal_stack = self._goals.pick_one()

        chosen_goal_stack.remove_completed()

        if chosen_goal_stack:
            chosen_goal_stack.take_action()

    def push_goal(self, priority: int, goal: Goal) -> None:
        """Add a goal to the AI"""
        # We assume that if someone is pushing a goal directly to the AIComponent, then
        # this is an independent stack of goals
        self._goals.append(priority, GoalStack([goal]))

    def to_dict(self) -> Dict[str, Any]:
        return {}
