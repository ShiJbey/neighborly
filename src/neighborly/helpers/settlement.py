"""Helper functions for managing Settlements.

"""

from __future__ import annotations

import random

from neighborly.components.settlement import District, Settlement
from neighborly.ecs import GameObject, World
from neighborly.libraries import DistrictLibrary, SettlementLibrary


def create_settlement(world: World, definition_id: str) -> GameObject:
    """Create a new settlement.

    Parameters
    ----------
    world
        The world instance to spawn the settlement in.
    definition_id
        The ID of the definition to instantiate.
    Returns
    -------
    GameObject
        The settlement.
    """
    library = world.resource_manager.get_resource(SettlementLibrary)

    settlement_def = library.get_definition(definition_id)

    settlement = world.gameobject_manager.spawn_gameobject(
        components=settlement_def.components
    )
    settlement.metadata["definition_id"] = definition_id

    library = settlement.world.resource_manager.get_resource(DistrictLibrary)
    rng = settlement.world.resource_manager.get_resource(random.Random)

    for district_entry in settlement_def.districts:
        if district_entry.with_id:

            district = create_district(
                settlement.world,
                district_entry.with_id,
            )

            add_district_to_settlement(settlement, district)

        elif district_entry.with_tags:

            matching_districts = library.get_definition_with_tags(
                district_entry.with_tags
            )

            if matching_districts:
                chosen_district = rng.choice(matching_districts)

                district = create_district(
                    settlement.world,
                    chosen_district.definition_id,
                )

                add_district_to_settlement(settlement, district)

    return settlement


def create_district(
    world: World,
    definition_id: str,
) -> GameObject:
    """Create a new district GameObject.

    Parameters
    ----------
    world
        The world instance spawn the district in.
    definition_id
        The ID of the definition to instantiate.

    Returns
    -------
    GameObject
        The district.
    """
    library = world.resource_manager.get_resource(DistrictLibrary)

    district_def = library.get_definition(definition_id)

    district = world.gameobject_manager.spawn_gameobject(
        components=district_def.components
    )
    district.metadata["definition_id"] = definition_id

    return district


def add_district_to_settlement(settlement: GameObject, district: GameObject) -> None:
    """Add a district to a settlement."""
    settlement.get_component(Settlement).add_district(district)
    district.get_component(District).settlement = settlement
    settlement.add_child(district)
