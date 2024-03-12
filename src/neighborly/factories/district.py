"""District Factory.

"""

from __future__ import annotations

from typing import Optional

import pydantic

from neighborly.ecs import GameObject, World


class DistrictGenerationOptions(pydantic.BaseModel):
    """Parameter overrides used when creating a new district GameObject."""

    definition_id: str
    """The definition to create."""
    name: Optional[str] = None
    """The name of the district."""


class DistrictFactory:
    """Creates instances of districts using definitions."""

    def instantiate(
        self, world: World, settlement: GameObject, options: DistrictGenerationOptions
    ) -> GameObject:
        """Create instance of district using the options.

        Parameters
        ----------
        world
            The simulation's world instance.
        settlement
            The settlement the district will belong to.
        options
            Generation options.
        """
        library = world.resources.get_resource(DistrictLibrary)

        district_def = library.get_definition(options.definition_id)

        district = world.gameobjects.spawn_gameobject()
        district.metadata["definition_id"] = options.definition_id

        district_def.initialize(settlement, district, options)

        settlement.get_component(Settlement).add_district(district)

        district.metadata["definition_id"] = self.definition_id

        district.add_component(
            District(
                name="",
                description="",
                settlement=settlement,
                residential_slots=self.residential_slots,
                business_slots=self.business_slots,
            )
        )

        self._initialize_name(district)
        self._initialize_business_spawn_table(district)
        self._initialize_character_spawn_table(district)
        self._initialize_residence_spawn_table(district)

        raise NotImplementedError()

    def _initialize_name(self, district: GameObject) -> None:
        """Generates a name for the district."""
        tracery = district.world.resources.get_resource(Tracery)
        name = tracery.generate(self.display_name)
        district.get_component(District).name = name
        district.name = name

    def _initialize_business_spawn_table(self, district: GameObject) -> None:
        """Create the business spawn table for the district."""
        world = district.world

        business_library = world.resources.get_resource(BusinessLibrary)

        table_entries: list[BusinessSpawnTableEntry] = []

        for entry in self.businesses:
            if isinstance(entry, str):
                business_def = business_library.get_definition(entry)
                table_entries.append(
                    BusinessSpawnTableEntry(
                        name=entry,
                        spawn_frequency=business_def.spawn_frequency,
                        max_instances=business_def.max_instances,
                        min_population=business_def.min_population,
                        instances=0,
                    )
                )
            else:
                business_def = business_library.get_definition(entry["definition_id"])

                table_entries.append(
                    BusinessSpawnTableEntry(
                        name=entry["definition_id"],
                        spawn_frequency=entry.get(
                            "spawn_frequency", business_def.spawn_frequency
                        ),
                        max_instances=entry.get(
                            "max_instances", business_def.max_instances
                        ),
                        min_population=entry.get(
                            "min_population", business_def.min_population
                        ),
                        instances=0,
                    )
                )

        district.add_component(BusinessSpawnTable(entries=table_entries))

    def _initialize_character_spawn_table(self, district: GameObject) -> None:
        """Create the character spawn table for the district."""
        world = district.world
        character_library = world.resources.get_resource(CharacterLibrary)

        table_entries: list[CharacterSpawnTableEntry] = []

        for entry in self.characters:

            character_def = character_library.get_definition(entry["definition_id"])

            table_entries.append(
                CharacterSpawnTableEntry(
                    name=entry["definition_id"],
                    spawn_frequency=entry.get(
                        "spawn_frequency", character_def.spawn_frequency
                    ),
                )
            )

        district.add_component(CharacterSpawnTable(entries=table_entries))

    def _initialize_residence_spawn_table(self, district: GameObject) -> None:
        """Create the residence spawn table for the district."""
        world = district.world
        residence_library = world.resources.get_resource(ResidenceLibrary)

        table_entries: list[ResidenceSpawnTableEntry] = []

        for entry in self.residences:
            # The entry is a string. We import all defaults from the main definition
            if isinstance(entry, str):
                residence_def = residence_library.get_definition(entry)
                table_entries.append(
                    ResidenceSpawnTableEntry(
                        name=entry,
                        spawn_frequency=residence_def.spawn_frequency,
                        instances=0,
                        required_population=residence_def.required_population,
                        max_instances=residence_def.max_instances,
                        is_multifamily=residence_def.is_multifamily,
                    )
                )

            # The entry is an object with overrides
            else:
                residence_def = residence_library.get_definition(entry["definition_id"])

                table_entries.append(
                    ResidenceSpawnTableEntry(
                        name=entry["definition_id"],
                        spawn_frequency=entry.get(
                            "spawn_frequency", residence_def.spawn_frequency
                        ),
                        instances=0,
                        required_population=entry.get(
                            "required_population", residence_def.required_population
                        ),
                        max_instances=entry.get(
                            "max_instances", residence_def.max_instances
                        ),
                        is_multifamily=residence_def.is_multifamily,
                    )
                )

        district.add_component(ResidenceSpawnTable(entries=table_entries))
