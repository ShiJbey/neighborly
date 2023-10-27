"""Helper functions for managing Settlements.

"""

from __future__ import annotations

from neighborly.components.settlement import Settlement
from neighborly.defs.base_types import DistrictDef, SettlementDef
from neighborly.ecs import GameObject, World
from neighborly.libraries import DistrictLibrary, SettlementLibrary


def create_settlement(world: World, definition_id: str) -> GameObject:
    """Create a new settlement.

    Parameters
    ----------
    world
        The world instance to spawn the settlement in.
    definition_id
        The definition to use to initialize the settlement.

    Returns
    -------
    GameObject
        The settlement.
    """
    settlement = world.gameobject_manager.spawn_gameobject()
    settlement.metadata["definition_id"] = definition_id

    settlement.add_component(Settlement(name=""))

    library = world.resource_manager.get_resource(SettlementLibrary)

    settlement_def = library.get_definition(definition_id)

    settlement_def.initialize(settlement)

    return settlement


def create_district(
    world: World, settlement: GameObject, definition_id: str
) -> GameObject:
    """Create a new district GameObject.

    Parameters
    ----------
    world
        The world instance spawn the district in.
    settlement
        The settlement that owns district belongs to.
    definition_id
        The definition to use to initialize the district.

    Returns
    -------
    GameObject
        The district.
    """
    library = world.resource_manager.get_resource(DistrictLibrary)

    district_def = library.get_definition(definition_id)

    district = world.gameobject_manager.spawn_gameobject()
    district.metadata["definition_id"] = definition_id

    district_def.initialize(settlement, district)

    settlement.get_component(Settlement).add_district(district)

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
