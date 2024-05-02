"""Trait Component Factories.

"""

# import random
from typing import Any

from neighborly.components.traits import Traits
from neighborly.ecs import Component, ComponentFactory, World


class TraitsFactory(ComponentFactory):
    """Creates Traits component instances."""

    __component__ = "Traits"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        return Traits()
