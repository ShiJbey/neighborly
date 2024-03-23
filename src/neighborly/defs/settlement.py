"""Settlement Factory.

"""

from __future__ import annotations

from neighborly.components.settlement import Settlement
from neighborly.defs.base_types import (
    DistrictGenOptions,
    SettlementDef,
    SettlementGenOptions,
)
from neighborly.ecs import GameObject, World
from neighborly.helpers.settlement import create_district
from neighborly.libraries import DistrictLibrary, SettlementLibrary
from neighborly.tracery import Tracery


class DefaultSettlementDef(SettlementDef):
    """Creates instances of settlements."""

    def instantiate(self, world: World, options: SettlementGenOptions) -> GameObject:
        """Create an instance of a settlement.

        Parameters
        ----------
        world
            The simulation's world instance
        options
            Generation options
        """

        settlement = GameObject.create_new(world)
        settlement.metadata["definition_id"] = options.definition_id

        settlement.add_component(Settlement, name="")

        library = world.resources.get_resource(SettlementLibrary)

        settlement_def = library.get_definition(options.definition_id)

        settlement.metadata["definition_id"] = options.definition_id
        self._initialize_name(settlement, settlement_def)
        self._initialize_districts(settlement, settlement_def)

        return settlement

    def _initialize_name(
        self, settlement: GameObject, settlement_def: SettlementDef
    ) -> None:
        """Generates a name for the settlement."""
        tracery = settlement.world.resources.get_resource(Tracery)
        settlement_name = tracery.generate(settlement_def.display_name)
        settlement.get_component(Settlement).name = settlement_name
        settlement.name = settlement_name

    def _initialize_districts(
        self, settlement: GameObject, settlement_def: SettlementDef
    ) -> None:
        """Instantiates the settlement's districts."""

        library = settlement.world.resources.get_resource(DistrictLibrary)
        rng = settlement.world.rng

        for district_entry in settlement_def.districts:
            if district_entry.with_id:
                district = create_district(
                    settlement.world,
                    settlement,
                    DistrictGenOptions(definition_id=district_entry.with_id),
                )
                settlement.add_child(district)
            elif district_entry.with_tags:
                matching_districts = library.get_definition_with_tags(
                    district_entry.with_tags
                )

                if matching_districts:
                    chosen_district = rng.choice(matching_districts)
                    district = create_district(
                        settlement.world,
                        settlement,
                        DistrictGenOptions(definition_id=chosen_district.definition_id),
                    )
                    settlement.add_child(district)
