"""Stat Component Factories."""

import random
from typing import Any, Type

from neighborly.components.stats import (
    Discipline,
    Fertility,
    Lifespan,
    Loyalty,
    Luck,
    RomancePropensity,
    Sociability,
    StatComponent,
    Stats,
    Stewardship,
    ViolencePropensity,
    WantForChildren,
    WantForMarriage,
    WantForPower,
    WantToWork,
)
from neighborly.ecs import Component, ComponentFactory, World


class StatsFactory(ComponentFactory):
    """Creates Stats component instances."""

    __component__ = "Stats"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return Stats()


class StatComponentFactory(ComponentFactory):
    """Parent class to facilitate factories definitions for other stats."""

    # Component intentionally left blank to trigger error if directly instantiated.
    __component__ = ""

    __slots__ = ("stat_component_type",)

    stat_component_type: Type[StatComponent]

    def __init__(
        self,
        stat_component_type: Type[StatComponent],
    ) -> None:
        super().__init__()
        self.stat_component_type = stat_component_type

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)

        value: float = float(kwargs.get("value", 0))

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return self.stat_component_type(base_value=value)


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


class RomancePropensityFactory(StatComponentFactory):
    """Creates instances of RomancePropensity Components."""

    __component__ = "RomancePropensity"

    def __init__(self) -> None:
        super().__init__(RomancePropensity)


class ViolencePropensityFactory(StatComponentFactory):
    """Creates instances of ViolencePropensity Components."""

    __component__ = "ViolencePropensity"

    def __init__(self) -> None:
        super().__init__(ViolencePropensity)


class LoyaltyFactory(StatComponentFactory):
    """Creates instances of Loyalty Components."""

    __component__ = "Loyalty"

    def __init__(self) -> None:
        super().__init__(Loyalty)


class WantForPowerFactory(StatComponentFactory):
    """Creates instances of WantForPower Components."""

    __component__ = "WantForPower"

    def __init__(self) -> None:
        super().__init__(WantForPower)


class WantForChildrenFactory(StatComponentFactory):
    """Creates instances of WantForChildren Components."""

    __component__ = "WantForChildren"

    def __init__(self) -> None:
        super().__init__(WantForChildren)


class WantToWorkFactory(StatComponentFactory):
    """Creates instances of WantToWork Components."""

    __component__ = "WantToWork"

    def __init__(self) -> None:
        super().__init__(WantToWork)


class LuckFactory(StatComponentFactory):
    """Creates instances of Luck Components."""

    __component__ = "Luck"

    def __init__(self) -> None:
        super().__init__(Luck)


class WantForMarriageFactory(StatComponentFactory):
    """Creates instances of WantForMarriage Components."""

    __component__ = "WantForMarriage"

    def __init__(self) -> None:
        super().__init__(WantForMarriage)
