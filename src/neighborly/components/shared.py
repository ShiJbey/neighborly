"""Shared component types.

"""

from __future__ import annotations

from typing import Any

from neighborly.ecs import Component


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
