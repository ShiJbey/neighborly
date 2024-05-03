"""Factories for residential building components.

"""

from typing import Any

from neighborly.components.location import Location
from neighborly.components.residence import ResidentialBuilding, ResidentialUnit, Vacant
from neighborly.components.traits import Traits
from neighborly.ecs import Component, ComponentFactory, GameObject, World
from neighborly.libraries import IResidenceFactory, ResidenceLibrary


class ResidentialBuildingFactory(ComponentFactory):
    """Creates ResidentialBuilding component instances."""

    __component__ = "ResidentialBuilding"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return ResidentialBuilding()


class DefaultResidenceFactory(IResidenceFactory):
    """Default implementation of a residence factory."""

    def create_residence(self, world: World, definition_id: str) -> GameObject:
        library = world.resource_manager.get_resource(ResidenceLibrary)

        residence_def = library.get_definition(definition_id)

        residence = world.gameobject_manager.spawn_gameobject(
            components=residence_def.components
        )
        residence.metadata["definition_id"] = definition_id

        world = residence.world
        building = residence.get_component(ResidentialBuilding)

        for _ in range(residence_def.residential_units):
            residential_unit = world.gameobject_manager.spawn_gameobject(
                name="ResidentialUnit"
            )
            residential_unit.add_component(Traits())
            residence.add_child(residential_unit)
            residential_unit.add_component(ResidentialUnit(building=residence))
            residential_unit.add_component(Location(is_private=True))
            building.add_residential_unit(residential_unit)
            residential_unit.add_component(Vacant())

        return residence
