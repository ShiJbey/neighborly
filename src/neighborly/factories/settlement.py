"""Settlement Component Factories.

"""

from typing import Any

from neighborly.components.settlement import District, Settlement
from neighborly.ecs import Component, ComponentFactory, World


class SettlementFactory(ComponentFactory):
    """Creates Settlement component instances."""

    __component__ = "Settlement"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        name = kwargs.get("name", "")

        if name_factory := kwargs.get("name_factory", ""):
            # factories = world.resource_manager.get_resource(SettlementNameFactories)

            # name = factories.get_factory(name_factory)(gameobject)
            del name_factory
            # TODO: Add the revised name factory
            name = ""

        return Settlement(name=name)


class DistrictFactory(ComponentFactory):
    """Creates District component instances."""

    __component__ = "District"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        name = kwargs.get("name", "")
        description = kwargs.get("description", "")
        business_slots: int = kwargs.get("business_slots", 0)
        residential_slots: int = kwargs.get("residential_slots", 0)

        if name_factory := kwargs.get("name_factory", ""):
            # factories = world.resource_manager.get_resource(DistrictNameFactories)

            # name = factories.get_factory(name_factory)(gameobject)
            del name_factory
            # TODO: Add the revised name factory
            name = ""

        return District(
            name=name,
            description=description,
            residential_slots=residential_slots,
            business_slots=business_slots,
        )
