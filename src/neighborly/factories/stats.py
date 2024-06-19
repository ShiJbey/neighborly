"""Stat Component Factories."""

import random
from typing import Any

from neighborly.components.stats import (
    Charm,
    Discipline,
    Fertility,
    Intelligence,
    Lifespan,
    Sociability,
    Stats,
    Stewardship,
)
from neighborly.ecs import Component, ComponentFactory, World


class StatsFactory(ComponentFactory):
    """Creates Stats component instances."""

    __component__ = "Stats"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return Stats()


class LifespanFactory(ComponentFactory):
    """Creates Lifespan component instances."""

    __component__ = "Lifespan"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Lifespan(base_value=value)


class FertilityFactory(ComponentFactory):
    """Creates Fertility component instances."""

    __component__ = "Fertility"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Fertility(base_value=value)


class StewardshipFactory(ComponentFactory):
    """Creates Stewardship component instances."""

    __component__ = "Stewardship"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Stewardship(base_value=value)


class SociabilityFactory(ComponentFactory):
    """Creates Sociability component instances."""

    __component__ = "Sociability"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Sociability(base_value=value)


class IntelligenceFactory(ComponentFactory):
    """Creates Intelligence component instances."""

    __component__ = "Intelligence"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Intelligence(base_value=value)


class DisciplineFactory(ComponentFactory):
    """Creates Discipline component instances."""

    __component__ = "Discipline"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Discipline(base_value=value)


class CharmFactory(ComponentFactory):
    """Creates Charm component instances."""

    __component__ = "Charm"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Charm(base_value=value)
