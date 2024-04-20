"""Spawn Table Component Factories.

"""

import random
from typing import Any

from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    BusinessSpawnTableEntry,
    CharacterSpawnTable,
    CharacterSpawnTableEntry,
    ResidenceSpawnTable,
    ResidenceSpawnTableEntry,
)
from neighborly.ecs import Component, ComponentFactory, GameObject
from neighborly.libraries import BusinessLibrary, CharacterLibrary, ResidenceLibrary


class CharacterSpawnTableFactory(ComponentFactory):
    """Creates CharacterSpawnTable components."""

    __component__ = "CharacterSpawnTable"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        world = gameobject.world
        rng = world.resource_manager.get_resource(random.Random)

        character_library = world.resource_manager.get_resource(CharacterLibrary)

        table_entries: list[CharacterSpawnTableEntry] = []

        character_types: list[dict[str, Any]] = kwargs.get("character_types", [])

        for entry in character_types:
            if entry["with_id"]:

                character_def = character_library.get_definition(entry["with_id"])

                table_entries.append(
                    CharacterSpawnTableEntry(
                        name=character_def.definition_id,
                        spawn_frequency=entry.get("spawn_frequency", 1),
                    )
                )

            elif entry["with_tags"]:

                potential_defs = character_library.get_definition_with_tags(
                    entry["with_tags"]
                )

                if not potential_defs:
                    continue

                character_def = rng.choice(potential_defs)

                table_entries.append(
                    CharacterSpawnTableEntry(
                        name=character_def.definition_id,
                        spawn_frequency=entry.get("spawn_frequency", 1),
                    )
                )

        return CharacterSpawnTable(gameobject, table_entries)


class BusinessSpawnTableFactory(ComponentFactory):
    """Creates BusinessSpawnTable instances."""

    __component__ = "BusinessSpawnTable"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        world = gameobject.world
        rng = world.resource_manager.get_resource(random.Random)
        business_library = world.resource_manager.get_resource(BusinessLibrary)

        table_entries: list[BusinessSpawnTableEntry] = []
        business_types: list[dict[str, Any]] = kwargs.get("business_types", [])

        for entry in business_types:
            if entry["with_id"]:
                business_def = business_library.get_definition(entry["with_id"])
                table_entries.append(
                    BusinessSpawnTableEntry(
                        name=entry["with_id"],
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
            elif entry["with_tags"]:
                potential_defs = business_library.get_definition_with_tags(
                    entry["with_tags"]
                )

                if not potential_defs:
                    continue

                business_def = rng.choice(potential_defs)

                table_entries.append(
                    BusinessSpawnTableEntry(
                        name=business_def.definition_id,
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

        return BusinessSpawnTable(gameobject, table_entries)


class ResidenceSpawnTableFactory(ComponentFactory):
    """Creates ResidenceSpawnTable instances."""

    __component__ = "ResidenceSpawnTable"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:
        world = gameobject.world
        rng = world.resource_manager.get_resource(random.Random)

        residence_library = world.resource_manager.get_resource(ResidenceLibrary)
        residence_types: list[dict[str, Any]] = kwargs.get("business_types", [])

        table_entries: list[ResidenceSpawnTableEntry] = []

        for entry in residence_types:
            if entry["with_id"]:
                residence_def = residence_library.get_definition(entry["with_id"])

                table_entries.append(
                    ResidenceSpawnTableEntry(
                        name=residence_def.definition_id,
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

            elif entry["with_tags"]:

                potential_defs = residence_library.get_definition_with_tags(
                    entry["with_tags"]
                )

                if not potential_defs:
                    continue

                residence_def = rng.choice(potential_defs)

                table_entries.append(
                    ResidenceSpawnTableEntry(
                        name=residence_def.definition_id,
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

        return ResidenceSpawnTable(gameobject, entries=table_entries)
