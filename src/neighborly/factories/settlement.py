"""Settlement Component Factories.

"""

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

        if name_factory := kwargs.get("name_factory", ""):
            factories = world.resource_manager.get_resource(DistrictNameFactories)

            name = factories.get_factory(name_factory)(world)

        return District(name=name)


class DefaultDistrictFactory(IDistrictFactory):
    """Default implementation of a district factory."""

    def create_district(self, world: World, definition_id: str) -> GameObject:
        library = world.resource_manager.get_resource(DistrictLibrary)

        district_def = library.get_definition(definition_id)

        district = world.gameobject_manager.spawn_gameobject(
            components=district_def.components
        )
        district.metadata["definition_id"] = definition_id
        district.name = district.get_component(District).name

        return district


class DefaultSettlementFactory(ISettlementFactory):
    """Default implementation of a settlement factory."""

    def create_settlement(self, world: World, definition_id: str) -> GameObject:

        library = world.resource_manager.get_resource(SettlementLibrary)

        settlement_def = library.get_definition(definition_id)

        settlement = world.gameobject_manager.spawn_gameobject(
            components=settlement_def.components
        ).get_component(Settlement)

        settlement.gameobject.metadata["definition_id"] = definition_id

        settlement.gameobject.name = settlement.name

        return settlement.gameobject
