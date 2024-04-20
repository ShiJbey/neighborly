"""Helper functions for managing Settlements.

"""

from __future__ import annotations

from typing import Optional

from neighborly.components.settlement import District, Settlement
from neighborly.defs.base_types import (
    DistrictDef,
    DistrictGenOptions,
    SettlementDef,
    SettlementGenOptions,
)
from neighborly.ecs import GameObject, World
from neighborly.libraries import DistrictLibrary, SettlementLibrary


def create_settlement(
    world: World, definition_id: str, options: Optional[SettlementGenOptions] = None
) -> GameObject:
    """Create a new settlement.

    Parameters
    ----------
    world
        The world instance to spawn the settlement in.
    definition_id
        The ID of the definition to instantiate.
    options
        Generation options.

    Returns
    -------
    GameObject
        The settlement.
    """
    library = world.resource_manager.get_resource(SettlementLibrary)

    settlement_def = library.get_definition(definition_id)

    options = options if options else SettlementGenOptions()

    settlement = settlement_def.instantiate(world, options)

    return settlement


def create_district(
    world: World,
    settlement: GameObject,
    definition_id: str,
    options: Optional[DistrictGenOptions] = None,
) -> GameObject:
    """Create a new district GameObject.

    Parameters
    ----------
    world
        The world instance spawn the district in.
    settlement
        The settlement that owns district belongs to.
    definition_id
        The ID of the definition to instantiate.
    options
        Generation options.

    Returns
    -------
    GameObject
        The district.
    """
    library = world.resource_manager.get_resource(DistrictLibrary)

    district_def = library.get_definition(definition_id)

    options = options if options else DistrictGenOptions()

    district = district_def.instantiate(world, settlement, options)

    settlement.get_component(Settlement).add_district(district)
    district.get_component(District).settlement = settlement

    return district


def register_settlement_def(world: World, definition: SettlementDef) -> None:
    """Add a new settlement definition for the SettlementLibrary.

    Parameters
    ----------
    world
        The world instance containing the settlement library.
    definition
        The definition to add.
    """
    world.resource_manager.get_resource(SettlementLibrary).add_definition(definition)


def register_district_def(world: World, definition: DistrictDef) -> None:
    """Add a new district definition for the DistrictLibrary.

    Parameters
    ----------
    world
        The world instance containing the district library.
    definition
        The definition to add.
    """
    world.resource_manager.get_resource(DistrictLibrary).add_definition(definition)
    world.resource_manager.get_resource(DistrictLibrary).add_definition(definition)
