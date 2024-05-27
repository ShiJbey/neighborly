"""Belief System Component Factories.

"""

from typing import Any

from neighborly.components.beliefs import AppliedBeliefs, HeldBeliefs
from neighborly.ecs import Component, ComponentFactory, World


class AgentBeliefsFactory(ComponentFactory):
    """Constructs AgentBeliefs component instances."""

    __component__ = "AgentBeliefs"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return HeldBeliefs()


class AppliedBeliefsFactory(ComponentFactory):
    """Constructs AppliedBeliefs component instances."""

    __component__ = "AppliedBeliefs"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return AppliedBeliefs()
