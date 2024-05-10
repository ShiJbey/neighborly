"""Neighborly Action System.

Actions are operations performed by agents. Each action has two probability scores.
The first how likely it is an agent will attempt the action, and the second describes
how likely the action is to succeed if it is attempted.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Protocol

from neighborly.ecs import World


class ActionConsideration(Protocol):
    """A callable that accepts an action and returns a probability value."""

    def __call__(self, action: Action) -> float:
        """Calculate a probability for the action."""
        raise NotImplementedError()


class Action(ABC):
    """An abstract base class for all actions that agents may perform."""

    __action_id__: ClassVar[str] = ""

    __slots__ = ("world", "is_silent")

    world: World
    """The simulation's World instance."""
    is_silent: bool
    """Should this event or sub-events emit life events."""

    def __init__(self, world: World, is_silent: bool = False) -> None:
        super().__init__()
        self.world = world
        self.is_silent = is_silent

        if not self.__action_id__:
            raise ValueError("Please specify the __action_id__ class variable.")

    @classmethod
    def action_id(cls) -> str:
        """The action's ID."""
        return cls.__action_id__

    @abstractmethod
    def execute(self) -> bool:
        """Executes the action.

        Returns
        -------
        bool
            True, if the action completed successfully.
        """

        raise NotImplementedError()
