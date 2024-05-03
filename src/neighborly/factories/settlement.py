"""Settlement Component Factories.

"""

import random
from typing import Any

from neighborly.components.settlement import District, Settlement
from neighborly.ecs import Component, ComponentFactory, GameObject, World
from neighborly.libraries import (
    DistrictLibrary,
    DistrictNameFactories,
    IDistrictFactory,
    ISettlementFactory,
    SettlementLibrary,
    SettlementNameFactories,
)


class SettlementFactory(ComponentFactory):
    """Creates Settlement component instances."""

    __component__ = "Settlement"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        name = kwargs.get("name", "")

        if name_factory := kwargs.get("name_factory", ""):
            factories = world.resource_manager.get_resource(SettlementNameFactories)

            name = factories.get_factory(name_factory)(world)

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
            factories = world.resource_manager.get_resource(DistrictNameFactories)

            name = factories.get_factory(name_factory)(world)

        return District(
            name=name,
            description=description,
            residential_slots=residential_slots,
            business_slots=business_slots,
        )


class DefaultDistrictFactory(IDistrictFactory):
    """Default implementation of a district factory."""

    def create_district(self, world: World, definition_id: str) -> GameObject:
        library = world.resource_manager.get_resource(DistrictLibrary)

        district_def = library.get_definition(definition_id)

        district = world.gameobject_manager.spawn_gameobject(
            components=district_def.components
        )
        district.metadata["definition_id"] = definition_id

        return district


class DefaultSettlementFactory(ISettlementFactory):
    """Default implementation of a settlement factory."""

    def create_settlement(self, world: World, definition_id: str) -> GameObject:

        library = world.resource_manager.get_resource(SettlementLibrary)
        district_library = world.resource_manager.get_resource(DistrictLibrary)

        settlement_def = library.get_definition(definition_id)

        settlement = world.gameobject_manager.spawn_gameobject(
            components=settlement_def.components
        )
        settlement.metadata["definition_id"] = definition_id

        library = settlement.world.resource_manager.get_resource(DistrictLibrary)
        rng = settlement.world.resource_manager.get_resource(random.Random)

        for district_entry in settlement_def.districts:
            if district_entry.with_id:

                district = district_library.factory.create_district(
                    settlement.world,
                    district_entry.with_id,
                )

                settlement.get_component(Settlement).add_district(district)
                district.get_component(District).settlement = settlement
                settlement.add_child(district)

            elif district_entry.with_tags:

                matching_districts = library.get_definition_with_tags(
                    district_entry.with_tags
                )

                if matching_districts:
                    chosen_district = rng.choice(matching_districts)

                    district = district_library.factory.create_district(
                        settlement.world,
                        chosen_district.definition_id,
                    )

                    settlement.get_component(Settlement).add_district(district)
                    district.get_component(District).settlement = settlement
                    settlement.add_child(district)

        return settlement
