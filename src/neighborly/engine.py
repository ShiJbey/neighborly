# -*- coding: utf-8 -*-
"""
engine.py

The Neighborly engine handles all the domain-specific content
for simulations. It is responsible for defining the authoring
interface
"""
from __future__ import annotations

import dataclasses
import logging
import random
from random import Random
from typing import Any, Dict, List, Optional, Protocol, Type

import pydantic

from neighborly.components.business import OccupationType
from neighborly.components.residence import ResidentialZoning
from neighborly.core.ecs import Component, GameObject, IComponentFactory, World
from neighborly.core.life_event import ILifeEvent
from neighborly.core.name_generation import TraceryNameFactory
from neighborly.core.settlement import Settlement
from neighborly.core.time import SimDateTime

logger = logging.getLogger(__name__)


#########################################
#  ARCHETYPES
#########################################


class ArchetypeNotFoundError(Exception):
    """Error thrown when an archetype is not found in the engine"""

    def __init__(self, archetype_name: str) -> None:
        super().__init__()
        self.archetype_name: str = archetype_name
        self.message: str = f"Could not find archetype with name '{archetype_name}'"

    def __str__(self) -> str:
        return self.message


class IArchetypeFactory(Protocol):
    """Interface for factories that construct GameObjects from a collection of components"""

    def __call__(self, world: World, **kwargs: Any) -> GameObject:
        """Create a new instance of this prefab"""
        raise NotImplementedError


class CharacterSpawnConfig(pydantic.BaseModel):
    """
    Configuration data regarding how this archetype should be spawned

    Attributes
    ----------
    spawn_frequency: int
        The relative frequency that this archetype should be
        chosen to spawn into the simulation
    spouse_archetypes: List[str]
        A list of regular expression strings used to match what
        other character archetypes can spawn as this a spouse
        to this character archetype
    chance_spawn_with_spouse: float
        The probability that a character will spawn with a spouse
    max_children_at_spawn: int
        The maximum number of children that a character can spawn
        with regardless of the presence of a spouse
    child_archetypes: List[str]
        A list of regular expression strings used to match what
        other character archetypes can spawn as a child to
        this character archetype
    """

    spawn_frequency: int = 1
    spouse_archetypes: List[str] = pydantic.Field(default_factory=list)
    chance_spawn_with_spouse: float = 0.5
    max_children_at_spawn: int = 3
    child_archetypes: List[str] = pydantic.Field(default_factory=list)


@dataclasses.dataclass
class CharacterArchetypeConfig:
    name: str
    factory: IArchetypeFactory
    spawn_config: CharacterSpawnConfig = dataclasses.field(
        default_factory=CharacterSpawnConfig
    )
    options: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def spawn(self, world: World, **kwargs: Any) -> GameObject:
        """Create an instance of this archetype"""
        return self.factory(world, **{**self.options, **kwargs})


class CharacterArchetypes:
    """Collection of factories that create character entities"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, CharacterArchetypeConfig] = {}

    def add(self, config: CharacterArchetypeConfig) -> None:
        """Register a new archetype by name"""
        if config.name in self._registry:
            logger.debug(f"Overwrote Character Archetype mapped to '{config.name}'")
        self._registry[config.name] = config

    def get_all(self) -> List[CharacterArchetypeConfig]:
        """Get all stored archetypes"""
        return list(self._registry.values())

    def get(self, name: str) -> CharacterArchetypeConfig:
        """Get an archetype by name"""
        try:
            return self._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)

    def choose_random(
        self,
        rng: random.Random,
    ) -> Optional[CharacterArchetypeConfig]:
        """Performs a weighted random selection across all character archetypes"""
        archetype_choices: List[CharacterArchetypeConfig] = []
        archetype_weights: List[int] = []

        for archetype in self.get_all():
            archetype_choices.append(archetype)
            archetype_weights.append(archetype.spawn_config.spawn_frequency)

        if archetype_choices:
            # Choose an archetype at random
            archetype = rng.choices(
                population=archetype_choices, weights=archetype_weights, k=1
            )[0]

            return archetype
        else:
            return None


class BusinessSpawnConfig(pydantic.BaseModel):
    """
    Configuration data regarding how this archetype should be spawned

    Attributes
    ----------
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
    """

    spawn_frequency: int = 1
    max_instances: int = 9999
    min_population: int = 0
    year_available: int = 0
    year_obsolete: int = 9999


@dataclasses.dataclass
class BusinessArchetypeConfig:
    name: str
    factory: IArchetypeFactory
    spawn_config: BusinessSpawnConfig = dataclasses.field(
        default_factory=BusinessSpawnConfig
    )
    options: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def spawn(self, world: World, **kwargs: Any) -> GameObject:
        """Create an instance of this archetype"""
        return self.factory(world, **{**self.options, **kwargs})


class BusinessArchetypes:
    """Collection factories that create business entities"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, BusinessArchetypeConfig] = {}

    def add(self, archetype: BusinessArchetypeConfig) -> None:
        """Register a new archetype by name"""
        if archetype.name in self._registry:
            logger.debug(f"Overwrote Business Archetype: ({archetype.name})")
        self._registry[archetype.name] = archetype

    def get_all(self) -> List[BusinessArchetypeConfig]:
        """Get all stored archetypes"""
        return list(self._registry.values())

    def get(self, name: str) -> BusinessArchetypeConfig:
        """Get an archetype by name"""
        try:
            return self._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)

    def choose_random(self, world: World) -> Optional[BusinessArchetypeConfig]:
        """
        Return all business archetypes that may be built
        given the state of the simulation
        """
        settlement = world.get_resource(Settlement)
        date = world.get_resource(SimDateTime)
        rng = world.get_resource(random.Random)

        archetype_choices: List[BusinessArchetypeConfig] = []
        archetype_weights: List[int] = []

        for archetype in self.get_all():
            if (
                settlement.business_counts[archetype.name]
                < archetype.spawn_config.max_instances
                and settlement.population >= archetype.spawn_config.min_population
                and (
                    archetype.spawn_config.year_available
                    <= date.year
                    < archetype.spawn_config.year_obsolete
                )
            ):
                archetype_choices.append(archetype)
                archetype_weights.append(archetype.spawn_config.spawn_frequency)

        if archetype_choices:
            # Choose an archetype at random
            archetype = rng.choices(
                population=archetype_choices, weights=archetype_weights, k=1
            )[0]

            return archetype

        return None


class ResidenceSpawnConfig(pydantic.BaseModel):
    """
    Configuration data regarding how this archetype should be spawned

    Attributes
    ----------
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
    residential_zoning: ResidentialZoning
        Marks this residence type as single or multi-family housing
    """

    spawn_frequency: int = 1
    max_instances: int = 9999
    min_population: int = 0
    year_available: int = 0
    year_obsolete: int = 9999
    residential_zoning: ResidentialZoning = ResidentialZoning.SingleFamily


@dataclasses.dataclass
class ResidenceArchetypeConfig:
    name: str
    factory: IArchetypeFactory
    spawn_config: ResidenceSpawnConfig = dataclasses.field(
        default_factory=ResidenceSpawnConfig
    )
    options: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def spawn(self, world: World, **kwargs: Any) -> GameObject:
        """Create an instance of this archetype"""
        return self.factory(world, **{**self.options, **kwargs})


class ResidenceArchetypes:
    """Collection factories that create residence entities"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, ResidenceArchetypeConfig] = {}

    def add(
        self,
        archetype: ResidenceArchetypeConfig,
    ) -> None:
        """Register a new archetype by name"""
        if archetype.name in self._registry:
            logger.debug(f"Overwrote Residence Archetype: ({archetype.name})")
        self._registry[archetype.name] = archetype

    def get_all(self) -> List[ResidenceArchetypeConfig]:
        """Get all stored archetypes"""
        return list(self._registry.values())

    def get(self, name: str) -> ResidenceArchetypeConfig:
        """Get an archetype by name"""
        try:
            return self._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)

    def choose_random(self, rng: Random) -> Optional[ResidenceArchetypeConfig]:
        archetype_choices: List[ResidenceArchetypeConfig] = []
        archetype_weights: List[int] = []
        for archetype in self.get_all():
            archetype_choices.append(archetype)
            archetype_weights.append(archetype.spawn_config.spawn_frequency)

        if archetype_choices:
            # Choose an archetype at random
            archetype = rng.choices(
                population=archetype_choices, weights=archetype_weights, k=1
            )[0]

            return archetype

        return None


#########################################
#  COMPONENT FACTORIES
#########################################


class DefaultComponentFactory(IComponentFactory):
    """Constructs instances of a component only using keyword parameters"""

    __slots__ = "component_type"

    def __init__(self, component_type: Type[Component]) -> None:
        super(IComponentFactory, self).__init__()
        self.component_type: Type[Component] = component_type

    def create(self, world: World, **kwargs: Any) -> Component:
        return self.component_type(**kwargs)


#########################################
#  THE ENGINE
#########################################


@dataclasses.dataclass(frozen=True)
class ComponentInfo:
    name: str
    component_type: Type[Component]
    factory: IComponentFactory


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
        "_rng",
        "_name_generator",
        "_component_types",
        "_character_archetypes",
        "_residence_archetypes",
        "_business_archetypes",
        "_occupation_types",
        "_inheritable_components",
    )

    def __init__(self, seed: Optional[int] = None) -> None:
        random.seed(seed)
        self._rng: random.Random = random.Random(seed)
        self._name_generator: TraceryNameFactory = TraceryNameFactory()
        self._component_types: Dict[str, ComponentInfo] = {}
        self._character_archetypes: CharacterArchetypes = CharacterArchetypes()
        self._residence_archetypes: ResidenceArchetypes = ResidenceArchetypes()
        self._business_archetypes: BusinessArchetypes = BusinessArchetypes()
        self._occupation_types: OccupationTypes = OccupationTypes()

    @property
    def rng(self) -> random.Random:
        return self._rng

    @property
    def name_generator(self) -> TraceryNameFactory:
        return self._name_generator

    @property
    def character_archetypes(self) -> CharacterArchetypes:
        return self._character_archetypes

    @property
    def residence_archetypes(self) -> ResidenceArchetypes:
        return self._residence_archetypes

    @property
    def business_archetypes(self) -> BusinessArchetypes:
        return self._business_archetypes

    @property
    def occupation_types(self) -> OccupationTypes:
        return self._occupation_types

    def get_component_info(self, component_name: str) -> ComponentInfo:
        return self._component_types[component_name]

    def register_component(
        self,
        component_type: Type[Component],
        name: Optional[str] = None,
        factory: Optional[IComponentFactory] = None,
    ) -> None:
        """
        Register component with the engine
        """
        component_name = name if name is not None else component_type.__name__
        self._component_types[component_name] = ComponentInfo(
            name=component_name,
            component_type=component_type,
            factory=(
                factory
                if factory is not None
                else DefaultComponentFactory(component_type)
            ),
        )


class LifeEvents:
    """
    Static class used to store instances of LifeEventTypes for
    use at runtime.
    """

    _registry: Dict[str, ILifeEvent] = {}

    @classmethod
    def add(cls, life_event: ILifeEvent, name: Optional[str] = None) -> None:
        """Register a new LifeEventType mapped to a name"""
        key_name = name if name else life_event.get_name()
        if key_name in cls._registry:
            logger.debug(f"Overwriting LifeEventType: ({key_name})")
        cls._registry[key_name] = life_event

    @classmethod
    def get_all(cls) -> List[ILifeEvent]:
        """Get all LifeEventTypes stores in the Library"""
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> ILifeEvent:
        """Get a LifeEventType using a name"""
        return cls._registry[name]


class OccupationTypes:
    """Collection OccupationType information for lookup at runtime"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, OccupationType] = {}

    def add(
        self,
        occupation_type: OccupationType,
        name: Optional[str] = None,
    ) -> None:
        entry_key = name if name else occupation_type.name
        if entry_key in self._registry:
            logger.debug(f"Overwriting OccupationType: ({entry_key})")
        self._registry[entry_key] = occupation_type

    def get(self, name: str) -> OccupationType:
        """
        Get an OccupationType by name

        Parameters
        ----------
        name: str
            The registered name of the OccupationType

        Returns
        -------
        OccupationType

        Raises
        ------
        KeyError
            When there is not an OccupationType
            registered to that name
        """
        return self._registry[name]
