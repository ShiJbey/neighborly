"""Belief System Component Factories.

"""

from typing import Any

from neighborly.components.beliefs import AgentBeliefs, AppliedBeliefs
from neighborly.ecs import Component, ComponentFactory, GameObject


class AgentBeliefsFactory(ComponentFactory):
    """Constructs AgentBeliefs component instances."""

    __component__ = "AgentBeliefs"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        return AgentBeliefs(gameobject)


class AppliedBeliefsFactory(ComponentFactory):
    """Constructs AppliedBeliefs component instances."""

    __component__ = "AppliedBeliefs"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        return AppliedBeliefs(gameobject)
