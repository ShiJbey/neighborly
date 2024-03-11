"""Helper functions for managing Settlements.

"""

from __future__ import annotations

from neighborly.components.settlement import Settlement
from neighborly.defs.base_types import (
    DistrictDef,
    DistrictGenerationOptions,
    SettlementDef,
    SettlementGenerationOptions,
)
from neighborly.ecs import GameObject, World
from neighborly.libraries import DistrictLibrary, SettlementLibrary


# Do we have to update so that it can do this with tags?
def create_settlement(world: World, options: SettlementGenerationOptions) -> GameObject:
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

    raise NotImplementedError()


def create_district(
    world: World, settlement: GameObject, options: DistrictGenerationOptions
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

    raise NotImplementedError()


def register_settlement_def(world: World, definition: SettlementDef) -> None:
    """Add a new settlement definition for the SettlementLibrary.

    Parameters
    ----------
    world
        The world instance containing the settlement library.
    definition
        The definition to add.
    """
    world.resources.get_resource(SettlementLibrary).add_definition(definition)


def register_district_def(world: World, definition: DistrictDef) -> None:
    """Add a new district definition for the DistrictLibrary.

    Parameters
    ----------
    world
        The world instance containing the district library.
    definition
        The definition to add.
    """
    world.resources.get_resource(DistrictLibrary).add_definition(definition)
