"""District Factory.

"""

from __future__ import annotations

from neighborly.components.settlement import District, Settlement
from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    BusinessSpawnTableEntry,
    CharacterSpawnTable,
    CharacterSpawnTableEntry,
    ResidenceSpawnTable,
    ResidenceSpawnTableEntry,
)
from neighborly.defs.base_types import DistrictDef, DistrictGenOptions
from neighborly.ecs import GameObject, World
from neighborly.libraries import BusinessLibrary, CharacterLibrary, ResidenceLibrary
from neighborly.tracery import Tracery


class DefaultDistrictDef(DistrictDef):
    """Creates instances of districts using definitions."""

    def instantiate(
        self, world: World, settlement: GameObject, options: DistrictGenOptions
    ) -> GameObject:

        district = GameObject.create_new(world)
        district.metadata["definition_id"] = options.definition_id

        district.metadata["definition_id"] = self.definition_id

        district.add_component(
            District,
            name="",
            description="",
            settlement=settlement,
            residential_slots=self.residential_slots,
            business_slots=self.business_slots,
        )

        self._initialize_name(district)
        self._initialize_business_spawn_table(district)
        self._initialize_character_spawn_table(district)
        self._initialize_residence_spawn_table(district)

        settlement.get_component(Settlement).districts.append(
            district.get_component(District)
        )

        return district

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

        spawn_table = district.add_component(BusinessSpawnTable)

        for entry in self.businesses:
            if entry.with_id:
                business_def = business_library.get_definition(entry.with_id)
                spawn_table.entries.append(
                    BusinessSpawnTableEntry(
                        name=entry.with_id,
                        spawn_frequency=business_def.spawn_frequency,
                        max_instances=business_def.max_instances,
                        min_population=business_def.min_population,
                        instances=0,
                    )
                )
            elif entry.with_tags:
                potential_defs = business_library.get_definition_with_tags(
                    entry.with_tags
                )

                if not potential_defs:
                    continue

                business_def = world.rng.choice(potential_defs)

                spawn_table.entries.append(
                    BusinessSpawnTableEntry(
                        name=business_def.definition_id,
                        spawn_frequency=entry.spawn_frequency,
                        max_instances=entry.max_instances,
                        min_population=entry.min_population,
                        instances=0,
                    )
                )

    def _initialize_character_spawn_table(self, district: GameObject) -> None:
        """Create the character spawn table for the district."""
        world = district.world
        character_library = world.resources.get_resource(CharacterLibrary)

        spawn_table = district.add_component(CharacterSpawnTable)

        for entry in self.characters:
            if entry.with_id:

                character_def = character_library.get_definition(entry.with_id)

                spawn_table.entries.append(
                    CharacterSpawnTableEntry(
                        name=character_def.definition_id,
                        spawn_frequency=entry.spawn_frequency,
                    )
                )

            elif entry.with_id:

                potential_defs = character_library.get_definition_with_tags(
                    entry.with_tags
                )

                if not potential_defs:
                    continue

                character_def = world.rng.choice(potential_defs)

                spawn_table.entries.append(
                    CharacterSpawnTableEntry(
                        name=character_def.definition_id,
                        spawn_frequency=entry.spawn_frequency,
                    )
                )

    def _initialize_residence_spawn_table(self, district: GameObject) -> None:
        """Create the residence spawn table for the district."""
        world = district.world

        residence_library = world.resources.get_resource(ResidenceLibrary)

        spawn_table = district.add_component(ResidenceSpawnTable)

        for entry in self.residences:
            if entry.with_id:
                residence_def = residence_library.get_definition(entry.with_id)

                spawn_table.entries.append(
                    ResidenceSpawnTableEntry(
                        name=residence_def.definition_id,
                        spawn_frequency=residence_def.spawn_frequency,
                        instances=0,
                        required_population=residence_def.required_population,
                        max_instances=residence_def.max_instances,
                        is_multifamily=residence_def.is_multifamily,
                    )
                )

            elif entry.with_tags:

                potential_defs = residence_library.get_definition_with_tags(
                    entry.with_tags
                )

                if not potential_defs:
                    continue

                residence_def = world.rng.choice(potential_defs)

                spawn_table.entries.append(
                    ResidenceSpawnTableEntry(
                        name=residence_def.definition_id,
                        spawn_frequency=residence_def.spawn_frequency,
                        instances=0,
                        required_population=residence_def.required_population,
                        max_instances=residence_def.max_instances,
                        is_multifamily=residence_def.is_multifamily,
                    )
                )
