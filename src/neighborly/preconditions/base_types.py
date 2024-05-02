"""Abstract base types for implementing preconditions.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from neighborly.ecs import World


class Precondition(ABC):
    """Abstract base class for all precondition objects."""

    __precondition_name__: ClassVar[str] = ""

    def __init__(self) -> None:
        super().__init__()
        if not self.__precondition_name__:
            raise ValueError(
                f"Please specify __precondition_name__ class attribute for {type(self)}"
            )

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a string description of the precondition."""
        raise NotImplementedError()

    @abstractmethod
    def check(self, blackboard: dict[str, Any]) -> bool:
        """Check if the precondition passes given a blackboard of values.

        Parameters
        ----------
        blackboard
            Information about the context of the precondition.

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

    @classmethod
    def precondition_name(cls) -> str:
        """Get the precondition name used in data files."""
        return cls.__precondition_name__

    def __str__(self) -> str:
        return self.description
