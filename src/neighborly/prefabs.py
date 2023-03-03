from __future__ import annotations

from typing import Set

import pydantic

from neighborly.core.ecs import EntityPrefab


class BusinessPrefab(EntityPrefab):
    """A prefab that specifically represents a Business that can spawn into the world

    Attributes
    ----------
    name: str
        The prefab's name
    is_template: bool, optional
        Is this prefab prohibited from being instantiated
        (defaults to False)
    extends: str, optional
        The name of the prefab that this one builds on
    spawn_frequency: int
        The relative frequency that this archetype should be
        chosen to spawn into the simulation
    max_instances: int
        The maximum number of instances of this archetype that may
        exist in the Settlement at any given time
    min_population: int
        The minimum number of characters that need to live in the
        settlement for this business to be available to spawn
    year_available: int
        The simulated year that this business archetype will be
        available to spawn
    year_obsolete: int
        The simulated year that this business archetype will no longer
        be available to spawn
    tags: Set[str]
        String tags for filtering
    """

    name: str
    spawn_frequency: int = 1
    max_instances: int = 9999
    min_population: int = 0
    year_available: int = 0
    year_obsolete: int = 9999
    is_template: bool = False
    extends: str = ""
    tags: Set[str] = pydantic.Field(default_factory=set)

    def get_owner_type(self) -> str:
        """Get the occupation name for owners of this business type"""
        try:
            return self.components["Business"]["owner_type"]
        except KeyError:
            raise RuntimeError(
                f"Cannot find owner_type in business prefab, {self.name}"
            )


class CharacterPrefab(EntityPrefab):
    """A prefab that specifically represents a character that can spawn into the world

    Attributes
    ----------
    name: str
        The prefab's name
    is_template: bool, optional
        Is this prefab prohibited from being instantiated
        (defaults to False)
    extends: str, optional
        The name of the prefab that this one builds on
    spawn_frequency: int
        The relative frequency that this archetype should be
        chosen to spawn into the simulation
    tags: Set[str]
        String tags for filtering
    """

    name: str
    spawn_frequency: int = 1
    is_template: bool = False
    extends: str = ""
    tags: Set[str] = pydantic.Field(default_factory=set)


class ResidencePrefab(EntityPrefab):
    """A prefab that specifically represents a residence that can spawn into the world

    Attributes
    ----------
    name: str
        The prefab's name
    is_template: bool, optional
        Is this prefab prohibited from being instantiated
        (defaults to False)
    extends: str, optional
        The name of the prefab that this one builds on
    spawn_frequency: int
        The relative frequency that this archetype should be
        chosen to spawn into the simulation
    max_instances: int
        The maximum number of instances of this archetype that may
        exist in the Settlement at any given time
    min_population: int
        The minimum number of characters that need to live in the
        settlement for this business to be available to spawn
    year_available: int
        The simulated year that this business archetype will be
        available to spawn
    year_obsolete: int
        The simulated year that this business archetype will no longer
        be available to spawn
    tags: Set[str]
        String tags for filtering
    """

    name: str
    is_template: bool = False
    extends: str = ""
    spawn_frequency: int = 1
    max_instances: int = 9999
    min_population: int = 0
    year_available: int = 0
    year_obsolete: int = 9999
    tags: Set[str] = pydantic.Field(default_factory=set)
