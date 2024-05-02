"""Helper functions for managing residences and residents.

"""

from __future__ import annotations

from neighborly.components.location import Location
from neighborly.components.residence import ResidentialBuilding, ResidentialUnit, Vacant
from neighborly.components.traits import Traits
from neighborly.ecs import GameObject, World
from neighborly.libraries import ResidenceLibrary


def create_residence(
    world: World,
    definition_id: str,
) -> GameObject:
    """Create a new residence instance."""
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
