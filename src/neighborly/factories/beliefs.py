"""Belief System Component Factories.

"""

from typing import Any

from neighborly.components.beliefs import HeldBeliefs
from neighborly.ecs import Component, ComponentFactory, World


class HeldBeliefsFactory(ComponentFactory):
    """Constructs HeldBeliefs component instances."""

    __component__ = "HeldBeliefs"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return HeldBeliefs()
