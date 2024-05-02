"""Factories for residential building components.

"""

from typing import Any

from neighborly.components.residence import ResidentialBuilding
from neighborly.ecs import Component, ComponentFactory, World


class ResidentialBuildingFactory(ComponentFactory):
    """Creates ResidentialBuilding component instances."""

    __component__ = "ResidentialBuilding"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return ResidentialBuilding()
