"""Shared Components.

This module contains components that are used in multiple GameObject types.

"""

from __future__ import annotations

from sqlalchemy.orm import Mapped

from neighborly.ecs import Component, GameData


class Agent(Component):
    """Represents an individual agent in the simulation."""

    __tablename__ = "agents"

    agent_type: Mapped[str]

    def __str__(self) -> str:
        return f"Agent({self.uid=}, {self.agent_type=})"

    def __repr__(self) -> str:
        return f"Agent({self.uid=}, {self.agent_type=})"


class Age(GameData):
    """A GameObject's age."""

    __tablename__ = "age"

    value: Mapped[int]
    gameobject: Mapped[int]

    def __str__(self) -> str:
        return f"Age({self.value!r})"

    def __repr__(self) -> str:
        return f"Age({self.value!r})"


class EventHistory(Component):
    """Stores a record of all past events for a specific GameObject."""

    __tablename__ = "event_history"

    # entries: Mapped[list[LifeEvent]] = relationship()
    # """A list of events in chronological-order."""
