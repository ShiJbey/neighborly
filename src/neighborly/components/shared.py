"""Shared component types.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from neighborly.ecs import Component, GameObject


class Age(Component):
    """Tracks the age of a GameObject in years."""

    __slots__ = ("_value",)

    _value: float
    """The age of the GameObject in simulated years."""

    def __init__(self, value: float = 0) -> None:
        super().__init__()
        self._value = value

    @property
    def value(self) -> float:
        """The age value."""
        return self._value

    @value.setter
    def value(self, value: float) -> None:
        """Set the age value."""

        self._value = value

    def to_dict(self) -> dict[str, Any]:
        return {"value": self._value}


class Modifier(ABC):
    """A modifier applied to a GameObject."""

    __slots__ = ("_source", "reason")

    _source: object
    """The source of the modifier."""
    reason: str
    """The reason for the modifier"""

    def __init__(self, source: Optional[object] = None, reason: str = "") -> None:
        super().__init__()
        self._source = source
        self.reason = reason

    @abstractmethod
    def get_description(self) -> str:
        """Get a description of what the modifier does."""

        raise NotImplementedError()

    @abstractmethod
    def is_expired(self) -> bool:
        """Return true if the modifier is no longer valid."""

        raise NotImplementedError()

    @abstractmethod
    def apply(self, target: GameObject) -> None:
        """Apply the effects of the modifier.."""

        raise NotImplementedError()

    @abstractmethod
    def remove(self, target: GameObject) -> None:
        """Remove the effects of this modifier."""

        raise NotImplementedError()

    @abstractmethod
    def update(self, target: GameObject) -> None:
        """Update the modifier for every time step that it is not expired."""

        raise NotImplementedError()

    def set_source(self, value: Optional[object]) -> None:
        """Set the source of the modifier."""

        self._source = value

    def get_source(self) -> Optional[object]:
        """Get the source of the modifier."""

        return self._source


class Modifiers(Component):
    """Manages all the modifiers attached to a GameObject."""

    __slots__ = ("modifiers",)

    modifiers: list[Modifier]
    """All modifiers within the manager."""

    def __init__(self) -> None:
        super().__init__()
        self.modifiers = []

    def add_modifier(self, modifier: Modifier) -> None:
        """Add a modifier to the manager."""
        self.modifiers.append(modifier)

    def remove_modifier(self, modifier: Modifier) -> bool:
        """Remove a modifier from the manager.

        Returns
        -------
        bool
            True if successfully removed.
        """
        try:
            self.modifiers.remove(modifier)
            return True
        except ValueError:
            return False

    def to_dict(self) -> dict[str, Any]:
        return {}
