"""Neighborly Create Default Settlement Plugin.

This plugin adds an initialization system that spawns a single settlement into the
world.

"""
import pathlib
from typing import Any, List, Union

from neighborly.command import SpawnSettlement
from neighborly.core.ecs import ISystem, World
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.systems import InitializationSystemGroup

plugin_info = PluginInfo(
    name="Create Default Settlement Plugin",
    plugin_id="default.create_settlement",
    version="0.1.0",
)

_AnyPath = Union[str, pathlib.Path]


class CreateDefaultSettlementSystem(ISystem):
    """This is a simple initialization system that creates a single settlement.

    By default, it instantiates a settlement GameObject using the GameObjectPrefab
    associated with the name, "settlement". If users want to change the prefab they
    should create a new prefab with the desired data and either (1) name it
    "settlement" to overwrite the existing prefab, or (2) change the name of the
    prefab the system looks for by updating the prefab_to_instantiate variable.
    """

    __slots__ = "prefab_to_instantiate"

    prefab_to_instantiate: str
    """The name of the settlement prefab to instantiate."""

    additional_character_tables: List[_AnyPath] = []
    """Spawn tables to extend the default character spawn table."""

    additional_business_tables: List[_AnyPath] = []
    """Spawn tables used to extend the default business spawn table."""

    additional_residence_tables: List[_AnyPath] = []
    """Spawn tables used to extend the default residence spawn table."""

    def __init__(self, prefab_to_instantiate: str = "settlement") -> None:
        super().__init__()
        self.prefab_to_instantiate = prefab_to_instantiate

    def on_update(self, world: World) -> None:
        settlement = (
            SpawnSettlement(self.prefab_to_instantiate).execute(world).get_result()
        )

        # factory = world.gameobject_manager.get_component_info(
        #     type(CharacterSpawnTable).__name__
        # ).factory
        #
        # extended_character_table = (
        #     settlement.get_component(CharacterSpawnTable)
        #     if settlement.has_component(CharacterSpawnTable)
        #     else CharacterSpawnTable()
        # )
        #
        # for path in self.additional_character_tables:
        #     table: CharacterSpawnTable = cast(
        #         CharacterSpawnTable, factory.create(world, path=path)
        #     )
        #     extended_character_table.extend(table)
        #
        # settlement.add_component(extended_character_table)
        #
        # extended_business_table = (
        #     settlement.get_component(BusinessSpawnTable)
        #     if settlement.has_component(BusinessSpawnTable)
        #     else BusinessSpawnTable()
        # )
        #
        # for path in self.additional_business_tables:
        #     table: BusinessSpawnTable = cast(
        #         BusinessSpawnTable, factory.create(world, path=path)
        #     )
        #     extended_business_table.extend(table)
        #
        # settlement.add_component(extended_business_table)
        #
        # extended_residence_table = (
        #     settlement.get_component(ResidenceSpawnTable)
        #     if settlement.has_component(ResidenceSpawnTable)
        #     else ResidenceSpawnTable()
        # )
        #
        # for path in self.additional_residence_tables:
        #     table: ResidenceSpawnTable = cast(
        #         ResidenceSpawnTable, factory.create(world, path=path)
        #     )
        #     extended_residence_table.extend(table)
        #
        # settlement.add_component(extended_residence_table)


def setup(sim: Neighborly, **kwargs: Any):
    sim.world.system_manager.add_system(
        CreateDefaultSettlementSystem(), system_group=InitializationSystemGroup
    )
