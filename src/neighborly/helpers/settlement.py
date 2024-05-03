"""Helper functions for managing Settlements.

"""

from __future__ import annotations

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

    return library.factory.create_settlement(world, definition_id)


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

    return library.factory.create_district(world, definition_id)
