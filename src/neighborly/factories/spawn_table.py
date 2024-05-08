"""Spawn Table Component Factories.

"""

from typing import Any

from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    BusinessSpawnTableEntry,
    CharacterSpawnTable,
    CharacterSpawnTableEntry,
    ResidenceSpawnTable,
    ResidenceSpawnTableEntry,
)
from neighborly.ecs import Component, ComponentFactory, World
from neighborly.libraries import BusinessLibrary, CharacterLibrary, ResidenceLibrary


class CharacterSpawnTableFactory(ComponentFactory):
    """Creates CharacterSpawnTable components."""

    __component__ = "CharacterSpawnTable"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        character_library = world.resource_manager.get_resource(CharacterLibrary)

        table_entries: list[CharacterSpawnTableEntry] = []

        character_types: list[dict[str, Any]] = kwargs.get("character_types", [])

        for entry in character_types:
            if definition_id := entry.get("with_id", ""):

                character_def = character_library.get_definition(definition_id)

                table_entries.append(
                    CharacterSpawnTableEntry(
                        definition_id=character_def.definition_id,
                        spawn_frequency=entry.get("spawn_frequency", 1),
                    )
                )

            elif definition_tags := entry.get("with_tags", []):

                matching_definitions = character_library.get_definition_with_tags(
                    definition_tags
                )

                for definition in matching_definitions:

                    table_entries.append(
                        CharacterSpawnTableEntry(
                            definition_id=definition.definition_id,
                            spawn_frequency=entry.get("spawn_frequency", 1),
                        )
                    )

        return CharacterSpawnTable(table_entries)


class BusinessSpawnTableFactory(ComponentFactory):
    """Creates BusinessSpawnTable instances."""

    __component__ = "BusinessSpawnTable"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        business_library = world.resource_manager.get_resource(BusinessLibrary)

        table_entries: list[BusinessSpawnTableEntry] = []
        business_types: list[dict[str, Any]] = kwargs.get("business_types", [])

        for entry in business_types:
            if definition_id := entry.get("with_id", ""):
                business_def = business_library.get_definition(definition_id)
                table_entries.append(
                    BusinessSpawnTableEntry(
                        definition_id=definition_id,
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
            elif definition_tags := entry.get("with_tags", []):
                matching_definitions = business_library.get_definition_with_tags(
                    definition_tags
                )

                for business_def in matching_definitions:

                    table_entries.append(
                        BusinessSpawnTableEntry(
                            definition_id=business_def.definition_id,
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

        return BusinessSpawnTable(table_entries)


class ResidenceSpawnTableFactory(ComponentFactory):
    """Creates ResidenceSpawnTable instances."""

    __component__ = "ResidenceSpawnTable"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        residence_library = world.resource_manager.get_resource(ResidenceLibrary)
        residence_types: list[dict[str, Any]] = kwargs.get("residence_types", [])

        table_entries: list[ResidenceSpawnTableEntry] = []

        for entry in residence_types:
            if definition_id := entry.get("with_id", ""):
                residence_def = residence_library.get_definition(definition_id)

                table_entries.append(
                    ResidenceSpawnTableEntry(
                        definition_id=residence_def.definition_id,
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

            elif definition_tags := entry.get("with_tags", []):

                matching_definitions = residence_library.get_definition_with_tags(
                    definition_tags
                )

                for residence_def in matching_definitions:

                    table_entries.append(
                        ResidenceSpawnTableEntry(
                            definition_id=residence_def.definition_id,
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

        return ResidenceSpawnTable(entries=table_entries)
