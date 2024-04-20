"""Business Component Factories.

"""

from typing import Any

from neighborly.components.business import Business, Occupation, Unemployed
from neighborly.ecs import Component, ComponentFactory, GameObject


class OccupationFactory(ComponentFactory):
    """Creates Occupation component instances."""

    __component__ = "Occupation"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        return Occupation(gameobject, **kwargs)


class BusinessFactory(ComponentFactory):
    """Creates Business component instances."""

    __component__ = "Business"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        return Business(gameobject, **kwargs)


class UnemployedFactory(ComponentFactory):
    """Creates Unemployed component instances."""

    __component__ = "Unemployed"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        return Unemployed(gameobject, **kwargs)
