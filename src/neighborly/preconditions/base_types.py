"""Abstract base types for implementing preconditions.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from neighborly.ecs import GameObject, World


class Precondition(ABC):
    """Abstract base class for all precondition objects."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a string description of the effect."""
        raise NotImplementedError()

    @abstractmethod
    def __call__(self, target: GameObject) -> bool:
        """Check if a GameObject passes the precondition.

        Parameters
        ----------
        target
            A GameObject

        Returns
        -------
        bool
            True if the gameobject passes the precondition, False otherwise.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        """Construct a new instance of the precondition using a data dict.

        Parameters
        ----------
        world
            The simulation's world instance
        params
            Keyword parameters to pass to the precondition.
        """
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.description
