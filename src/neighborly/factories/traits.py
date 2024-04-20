"""Trait Component Factories.

"""

from typing import Any

from neighborly.components.traits import Traits
from neighborly.ecs import Component, ComponentFactory, GameObject


class TraitsFactory(ComponentFactory):
    """Creates Traits component instances."""

    __component__ = "Traits"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        return Traits(gameobject)
