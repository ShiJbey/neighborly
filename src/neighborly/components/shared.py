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


class Agent(Component):
    """Marks the gameobject as being an agent."""

    __slots__ = ("_agent_type",)

    _agent_type: str
    """The type of agent represented by this GameObject."""

    def __init__(self, agent_type: str) -> None:
        super().__init__()
        self._agent_type = agent_type

    @property
    def agent_type(self) -> str:
        """The type of the agent."""
        return self._agent_type

    def to_dict(self) -> dict[str, Any]:
        return {"agent_type": self.agent_type}
