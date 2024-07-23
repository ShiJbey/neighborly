"""Stat Component Factories."""

import random
from typing import Any, Type

from neighborly.components.stats import (
    Boldness,
    Compassion,
    Diplomacy,
    Fertility,
    Greed,
    Honor,
    Intrigue,
    Learning,
    Lifespan,
    Luck,
    Martial,
    Prowess,
    Rationality,
    RomancePropensity,
    Sociability,
    StatComponent,
    Stats,
    Stewardship,
    Vengefulness,
    ViolencePropensity,
    WantForChildren,
    WantForMarriage,
    WantForPower,
    WantToWork,
    Zeal,
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


class MartialFactory(StatComponentFactory):
    """Creates Martial component instances."""

    __component__ = "Martial"

    def __init__(self) -> None:
        super().__init__(Martial)


class IntrigueFactory(StatComponentFactory):
    """Creates Intrigue component instances."""

    __component__ = "Intrigue"

    def __init__(self) -> None:
        super().__init__(Intrigue)


class LearningFactory(StatComponentFactory):
    """Creates Learning component instances."""

    __component__ = "Learning"

    def __init__(self) -> None:
        super().__init__(Learning)


class ProwessFactory(StatComponentFactory):
    """Creates Prowess component instances."""

    __component__ = "Prowess"

    def __init__(self) -> None:
        super().__init__(Prowess)


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


class HonorFactory(StatComponentFactory):
    """Creates Honor component instances."""

    __component__ = "Honor"

    def __init__(self) -> None:
        super().__init__(Honor)


class BoldnessFactory(StatComponentFactory):
    """Creates Boldness component instances."""

    __component__ = "Boldness"

    def __init__(self) -> None:
        super().__init__(Boldness)


class CompassionFactory(StatComponentFactory):
    """Creates Compassion component instances."""

    __component__ = "Compassion"

    def __init__(self) -> None:
        super().__init__(Compassion)


class DiplomacyFactory(StatComponentFactory):
    """Creates Diplomacy component instances."""

    __component__ = "Diplomacy"

    def __init__(self) -> None:
        super().__init__(Diplomacy)


class GreedFactory(StatComponentFactory):
    """Creates Greed component instances."""

    __component__ = "Greed"

    def __init__(self) -> None:
        super().__init__(Greed)


class RationalityFactory(StatComponentFactory):
    """Creates Rationality component instances."""

    __component__ = "Rationality"

    def __init__(self) -> None:
        super().__init__(Rationality)


class VengefulnessFactory(StatComponentFactory):
    """Creates Vengefulness component instances."""

    __component__ = "Vengefulness"

    def __init__(self) -> None:
        super().__init__(Vengefulness)


class ZealFactory(StatComponentFactory):
    """Creates Zeal component instances."""

    __component__ = "Zeal"

    def __init__(self) -> None:
        super().__init__(Zeal)


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
