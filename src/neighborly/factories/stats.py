"""Stat Component Factories."""

import random
from typing import Any

from neighborly.components.stats import (
    Charm,
    Courage,
    Discipline,
    Fertility,
    Intelligence,
    Kindness,
    Lifespan,
    Sociability,
    Stats,
    Stewardship,
)
from neighborly.ecs import Component, ComponentFactory, GameObject


class StatsFactory(ComponentFactory):
    """Creates Stats component instances."""

    __component__ = "Stats"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        return Stats(gameobject)


class LifespanFactory(ComponentFactory):
    """Creates Lifespan component instances."""

    __component__ = "Lifespan"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Lifespan(gameobject, base_value=value)


class FertilityFactory(ComponentFactory):
    """Creates Fertility component instances."""

    __component__ = "Fertility"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Fertility(gameobject, base_value=value)


class KindnessFactory(ComponentFactory):
    """Creates Kindness component instances."""

    __component__ = "Kindness"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Kindness(gameobject, base_value=value)


class CourageFactory(ComponentFactory):
    """Creates Courage component instances."""

    __component__ = "Courage"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Courage(gameobject, base_value=value)


class StewardshipFactory(ComponentFactory):
    """Creates Stewardship component instances."""

    __component__ = "Stewardship"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Stewardship(gameobject, base_value=value)


class SociabilityFactory(ComponentFactory):
    """Creates Sociability component instances."""

    __component__ = "Sociability"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Sociability(gameobject, base_value=value)


class IntelligenceFactory(ComponentFactory):
    """Creates Intelligence component instances."""

    __component__ = "Intelligence"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Intelligence(gameobject, base_value=value)


class DisciplineFactory(ComponentFactory):
    """Creates Discipline component instances."""

    __component__ = "Discipline"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Discipline(gameobject, base_value=value)


class CharmFactory(ComponentFactory):
    """Creates Charm component instances."""

    __component__ = "Charm"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        rng = gameobject.world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Charm(gameobject, base_value=value)
