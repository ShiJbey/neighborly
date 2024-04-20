"""Settlement Component Factories.

"""

from typing import Any

from neighborly.components.settlement import District, Settlement
from neighborly.defs.base_types import DistrictGenOptions, SettlementGenOptions
from neighborly.ecs import Component, ComponentFactory, GameObject
from neighborly.libraries import DistrictNameFactories, SettlementNameFactories


class SettlementFactory(ComponentFactory):
    """Creates Settlement component instances."""

    __component__ = "Settlement"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        world = gameobject.world

        name_factories = world.resources.get_resource(SettlementNameFactories)

        name = kwargs.get("name", "")

        if name_factory := kwargs.get("name_factory", ""):
            name = name_factories.get_factory(name_factory)(
                world, SettlementGenOptions()
            )

        return Settlement(gameobject, name=name)


class DistrictFactory(ComponentFactory):
    """Creates District component instances."""

    __component__ = "District"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        world = gameobject.world

        name_factories = world.resources.get_resource(DistrictNameFactories)

        name = kwargs.get("name", "")
        description = kwargs.get("description", "")
        business_slots: int = kwargs.get("business_slots", 0)
        residential_slots: int = kwargs.get("residential_slots", 0)

        if name_factory := kwargs.get("name_factory", ""):
            name = name_factories.get_factory(name_factory)(world, DistrictGenOptions())

        return District(
            gameobject,
            name=name,
            description=description,
            residential_slots=residential_slots,
            business_slots=business_slots,
        )
