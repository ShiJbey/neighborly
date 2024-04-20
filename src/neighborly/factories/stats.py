"""Stat Component Factories."""

from typing import Any

from neighborly.components.stats import Stats
from neighborly.ecs import Component, ComponentFactory, GameObject


class StatsFactory(ComponentFactory):
    """Creates Stats component instances."""

    __component__ = "Stats"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        return Stats(gameobject)
