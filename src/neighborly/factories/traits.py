"""Trait Component Factories.

"""

# import random
from typing import Any

from neighborly.components.traits import Traits
from neighborly.ecs import Component, ComponentFactory, GameObject


class TraitsFactory(ComponentFactory):
    """Creates Traits component instances."""

    __component__ = "Traits"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        traits = Traits(gameobject)

        return traits
