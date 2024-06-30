"""Abstract base types for implementing Effects.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from neighborly.ecs import GameObject, World


class Effect(ABC):
    """Abstract base class for all effect objects."""

    __effect_name__: ClassVar[str] = ""

    __slots__ = ("reason",)

    reason: str
    """The reason for the effect."""

    def __init__(self, reason: str = "") -> None:
        super().__init__()
        if not self.__effect_name__:
            raise ValueError(
                f"Please specify __effect_name__ class attribute for {type(self)}"
            )
        self.reason = reason

    @property
    @abstractmethod
    def description(self) -> str:
        """Get a string description of the effect."""
        raise NotImplementedError()

    @abstractmethod
    def apply(self, target: GameObject) -> None:
        """Apply the effects of this effect."""
        raise NotImplementedError()

    @abstractmethod
    def remove(self, target: GameObject) -> None:
        """Remove the effects of this effect."""
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        """Construct a new instance of the effect type using a data dict."""
        raise NotImplementedError()

    @classmethod
    def effect_name(cls) -> str:
        """Get the effect name used in data files."""
        return cls.__effect_name__

    def __str__(self) -> str:
        return self.description
