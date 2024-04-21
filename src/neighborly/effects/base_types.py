"""Abstract base types for implementing Effects.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from neighborly.ecs import GameObject, World


class Effect(ABC):
    """Abstract base class for all effect objects."""

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

    def __str__(self) -> str:
        return self.description
