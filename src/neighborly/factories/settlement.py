"""Settlement Factory.

"""

from __future__ import annotations

import pydantic

from neighborly.ecs import GameObject, World


class SettlementGenerationOptions(pydantic.BaseModel):
    """Parameters used when generating new settlements."""

    definition_id: str
    """The definition to generate."""
    name: str = ""
    """The name of the settlement."""


class SettlementFactory:
    """Creates instances of settlements."""

    def instantiate(
        self, world: World, options: SettlementGenerationOptions
    ) -> GameObject:
        """Create an instance of a settlement.

        Parameters
        ----------
        world
            The simulation's world instance
        options
            Generation options
        """

        settlement = world.gameobjects.spawn_gameobject()
        settlement.metadata["definition_id"] = options.definition_id

        settlement.add_component(Settlement(name=""))

        library = world.resources.get_resource(SettlementLibrary)

        settlement_def = library.get_definition(options.definition_id)

        settlement_def.initialize(settlement, options)

        settlement.metadata["definition_id"] = self.definition_id
        self.initialize_name(settlement)
        self.initialize_districts(settlement)

        raise NotImplementedError()

    def initialize_name(self, settlement: GameObject) -> None:
        """Generates a name for the settlement."""
        tracery = settlement.world.resources.get_resource(Tracery)
        settlement_name = tracery.generate(self.display_name)
        settlement.get_component(Settlement).name = settlement_name
        settlement.name = settlement_name

    def initialize_districts(self, settlement: GameObject) -> None:
        """Instantiates the settlement's districts."""

        # loop through a list of dictionary entry in self.districts, entry is settlement def strictint entry, entry go through ifs
        # if entry.id: if an id exists
        # elif entry.tags: Go through the tags
        # else: raise Error("Must specify tags or id")

        library = settlement.world.resources.get_resource(DistrictLibrary)
        rng = settlement.world.resources.get_resource(random.Random)

        for district_entry in self.districts:
            if district_entry.defintion_id:
                district = create_district(
                    settlement.world, settlement, district_entry.defintion_id
                )
                settlement.add_child(district)
            elif district_entry.tags:
                matching_districts = library.get_with_tags(district_entry.tags)

                if matching_districts:
                    chosen_district = rng.choice(matching_districts)
                    district = create_district(
                        settlement.world, settlement, chosen_district.definition_id
                    )
                    settlement.add_child(district)

            else:
                raise ValueError("Must specify tags or id")

        # for definition_id in self.districts:
        #     district = create_district(settlement.world, settlement, definition_id)
        #     settlement.add_child(district)
        # Old version
