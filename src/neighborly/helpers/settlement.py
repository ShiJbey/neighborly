"""Helper functions for managing Settlements.

"""

from __future__ import annotations

from neighborly.defs.base_types import DistrictGenOptions, SettlementGenOptions
from neighborly.ecs import GameObject, World
from neighborly.libraries import DistrictLibrary, SettlementLibrary


# Do we have to update so that it can do this with tags?
def create_settlement(world: World, options: SettlementGenOptions) -> GameObject:
    """Create a new settlement.

    Parameters
    ----------
    world
        The world instance to spawn the settlement in.
    options
        Generation options.

    Returns
    -------
    GameObject
        The settlement.
    """

    return (
        world.resources.get_resource(SettlementLibrary)
        .get_definition(options.definition_id)
        .instantiate(world, options)
    )


def create_district(
    world: World, settlement: GameObject, options: DistrictGenOptions
) -> GameObject:
    """Create a new district GameObject.

    Parameters
    ----------
    world
        The world instance spawn the district in.
    settlement
        The settlement that owns district belongs to.
    options
        Generation options.

    Returns
    -------
    GameObject
        The district.
    """

    return (
        world.resources.get_resource(DistrictLibrary)
        .get_definition(options.definition_id)
        .instantiate(world, settlement, options)
    )
