"""Shared Components.

This module contains components that are used in multiple GameObject types.

"""

from __future__ import annotations

from typing import Any, Iterable

from neighborly.ecs import Component
from neighborly.life_event import LifeEvent


class Agent(Component):
    """An agent in the agent-based modeling sense.

    Agents can form relationships with other agents. Agents can be individual
    characters, groups, key items, factions, religions, etc.
    """

    __slots__ = ("_agent_type",)

    _agent_type: str
    """What kind of agent this is."""

    def __init__(self, agent_type: str) -> None:
        super().__init__()
        self._agent_type = agent_type

    @property
    def agent_type(self) -> str:
        """What kind of agent this is."""
        return self._agent_type

    def to_dict(self) -> dict[str, Any]:
        return {"agent_type": self.agent_type}


class PersonalEventHistory(Component):
    """Stores a record of all past events for a specific GameObject."""

    __slots__ = ("_history",)

    _history: list[LifeEvent]
    """A list of events in chronological-order."""

    def __init__(self) -> None:
        super().__init__()
        self._history = []

    @property
    def history(self) -> Iterable[LifeEvent]:
        """A collection of events in chronological-order."""
        return self._history

    def append(self, event: LifeEvent) -> None:
        """Record a new life event.

        Parameters
        ----------
        event
            The event to record.
        """
        self._history.append(event)

    def to_dict(self) -> dict[str, Any]:
        return {"events": [id(e) for e in self._history]}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        history = [f"{type(e).__name__}({id(e)})" for e in self._history]
        return f"{self.__class__.__name__}({history})"
