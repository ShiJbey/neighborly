from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Type

from neighborly.core.ecs import Component, EntityArchetype, GameObject, World
from neighborly.core.name_generation import TraceryNameFactory


@dataclass
class CharacterInfo:
    """Information used when spawning new characters into the simulation"""

    spawn_multiplier: int = 1


@dataclass
class BusinessInfo:
    """Information used when spawning new characters into the simulation"""

    spawn_multiplier: int = 1
    min_population: int = 1
    max_instances: int = 9999


@dataclass
class ResidenceInfo:
    """Information used when spawning new characters into the simulation"""

    spawn_multiplier: int = 1


class ArchetypeNotFoundError(Exception):
    """Error thrown when an archetype is not found in the engine"""

    def __init__(self, archetype_name: str) -> None:
        super().__init__()
        self.archetype_name: str = archetype_name
        self.message: str = f"Could not find archetype with name '{archetype_name}'"

    def __str__(self) -> str:
        return self.message


class NeighborlyEngine:
    """
    An engine stores and instantiates entity archetypes for characters, businesses,
    residences, and other places.

    There should only be one NeighborlyEngine instance per simulation. It is designed
    to handle the internal logic of determining when to create certain entities. For
    example, the engine creates characters entities using spawn multipliers associated
    with each archetype.
    """

    __slots__ = (
        "_business_archetypes",
        "_residence_archetypes",
        "_character_archetypes",
        "_rng",
        "_name_generator",
        "_component_types",
    )

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng: random.Random = random.Random(seed)
        self._name_generator: TraceryNameFactory = TraceryNameFactory()
        self._component_types: Dict[str, Type[Component]] = {}
        self._character_archetypes: Dict[
            str, Tuple[EntityArchetype, CharacterInfo]
        ] = {}
        self._business_archetypes: Dict[str, Tuple[EntityArchetype, BusinessInfo]] = {}
        self._residence_archetypes: Dict[
            str, Tuple[EntityArchetype, ResidenceInfo]
        ] = {}

    @property
    def rng(self) -> random.Random:
        return self._rng

    @property
    def name_generator(self) -> TraceryNameFactory:
        return self._name_generator

    def add_component(self, component_type: Type[Component]) -> None:
        self._component_types[component_type.__name__] = component_type

    def add_character_archetype(
        self, archetype: EntityArchetype, spawn_multiplier: int = 1
    ) -> None:
        """
        Add a character archetype to the engine and set its spawn multiplier

        Parameters
        ----------
        archetype: EntityArchetype
            The archetype to add to the engine
        spawn_multiplier: (optional) int
            The multiplier used when determining what archetype to spawn next.
            The higher the multiplier, the more likely the archetype is to
            spawn.
        """
        self._character_archetypes[archetype.name] = (
            archetype,
            CharacterInfo(spawn_multiplier=spawn_multiplier),
        )

    def add_residence_archetype(
        self, archetype: EntityArchetype, spawn_multiplier: int = 1
    ) -> None:
        self._residence_archetypes[archetype.name] = (
            archetype,
            ResidenceInfo(spawn_multiplier=spawn_multiplier),
        )

    def add_business_archetype(
        self,
        archetype: EntityArchetype,
        min_population: int = 0,
        max_instances: int = 9999,
        spawn_multiplier: int = 1,
    ) -> None:
        self._business_archetypes[archetype.name] = (
            archetype,
            BusinessInfo(
                min_population=min_population,
                max_instances=max_instances,
                spawn_multiplier=spawn_multiplier,
            ),
        )

    def spawn_character(
        self, world, archetype_name: Optional[str] = None
    ) -> GameObject:
        """
        Spawn a new character GameObject into the world using a given or randomly-selected archetype

        Parameters
        ----------
        world: World
            World instance to add the character to
        archetype_name: Optional[str]
            Archetype name to spawn

        Returns
        -------
        GameObject
            The gameobject spawned into the world
        """
        if archetype_name is not None:
            try:
                archetype = self._character_archetypes[archetype_name][0]
            except KeyError:
                raise ArchetypeNotFoundError(archetype_name)

            character = world.spawn_archetype(archetype)
            return character
        else:
            archetype_choices: List[EntityArchetype] = []
            archetype_weights: List[int] = []
            for _, (archetype, info) in self._character_archetypes.items():
                archetype_choices.append(archetype)
                archetype_weights.append(info.spawn_multiplier)

            if archetype_choices:
                # Choose an archetype at random
                archetype: EntityArchetype = random.choices(
                    population=archetype_choices, weights=archetype_weights, k=1
                )[0]

                character = world.spawn_archetype(archetype)
                return character
            else:
                raise ArchetypeNotFoundError("")

    def spawn_business(
        self, world: World, population: int, archetype_name: Optional[str] = None
    ) -> GameObject:
        if archetype_name is not None:
            try:
                archetype = self._business_archetypes[archetype_name][0]
            except KeyError:
                raise ArchetypeNotFoundError(archetype_name)

            business = world.spawn_archetype(archetype)
            return business
        else:
            archetype_choices: List[EntityArchetype] = []
            archetype_weights: List[int] = []
            for archetype, info in self.get_eligible_business_archetypes(population):
                archetype_choices.append(archetype)
                archetype_weights.append(info.spawn_multiplier)

            if archetype_choices:
                # Choose an archetype at random
                archetype: EntityArchetype = random.choices(
                    population=archetype_choices, weights=archetype_weights, k=1
                )[0]

                business = world.spawn_archetype(archetype)
                return business

    def spawn_residence(
        self, world: World, archetype_name: Optional[str] = None
    ) -> GameObject:
        if archetype_name is not None:
            try:
                archetype = self._residence_archetypes[archetype_name][0]
            except KeyError:
                raise ArchetypeNotFoundError(archetype_name)

            residence = world.spawn_archetype(archetype)
            return residence
        else:
            archetype_choices: List[EntityArchetype] = []
            archetype_weights: List[int] = []
            for _, (archetype, info) in self._residence_archetypes.items():
                archetype_choices.append(archetype)
                archetype_weights.append(info.spawn_multiplier)

            # Choose an archetype at random
            archetype: EntityArchetype = random.choices(
                population=archetype_choices, weights=archetype_weights, k=1
            )[0]

            residence = world.spawn_archetype(archetype)
            return residence

    def get_eligible_business_archetypes(
        self, population: int
    ) -> List[Tuple[EntityArchetype, BusinessInfo]]:
        """
        Return all business archetypes that may be built
        given the state of the simulation
        """
        eligible_types = []

        for archetype, info in self._business_archetypes.values():
            if (
                archetype.instances < info.max_instances
                and population >= info.min_population
            ):
                eligible_types.append((archetype, info))

        return eligible_types
