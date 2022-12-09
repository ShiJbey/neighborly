# -*- coding: utf-8 -*-
"""
engine.py

The Neighborly engine handles all the domain-specific content
for simulations. It is responsible for defining the authoring
interface
"""
from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from random import Random
from typing import Any, Dict, List, Optional, Type

from neighborly.components.business import OccupationType
from neighborly.components.residence import ResidentialZoning
from neighborly.core.ecs import Component, GameObject, IComponentFactory, World
from neighborly.core.life_event import ILifeEvent
from neighborly.core.name_generation import TraceryNameFactory

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


class IEntityArchetype(ABC):
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this archetype"""
        raise NotImplementedError

    @abstractmethod
    def create(self, world: World, **kwargs: Any) -> GameObject:
        """Create a new instance of this prefab"""
        raise NotImplementedError


class ICharacterArchetype(IEntityArchetype):
    """Interface for archetypes that construct characters"""

    @abstractmethod
    def get_max_children_at_spawn(self) -> int:
        """Return the maximum amount of children this prefab can have when spawning"""
        raise NotImplementedError

    @abstractmethod
    def get_spawn_frequency(self) -> int:
        """Return the relative frequency that this prefab appears"""
        raise NotImplementedError

    @abstractmethod
    def get_chance_spawn_with_spouse(self) -> float:
        """Return the chance that a character from this prefab spawns with a spouse"""
        raise NotImplementedError


class IBusinessArchetype(IEntityArchetype):
    """Interface for archetypes that construct businesses"""

    @abstractmethod
    def get_min_population(self) -> int:
        """Return the minimum population needed for this business to be constructed"""
        raise NotImplementedError

    @abstractmethod
    def get_spawn_frequency(self) -> int:
        """Return the relative frequency that this prefab appears"""
        raise NotImplementedError

    @abstractmethod
    def get_year_available(self) -> int:
        """Return the year that this business is available to construct"""
        raise NotImplementedError

    @abstractmethod
    def get_year_obsolete(self) -> int:
        """Return the year that this business is no longer available to construct"""
        raise NotImplementedError

    @abstractmethod
    def get_instances(self) -> int:
        """Get the number of active instances of this archetype"""
        raise NotImplementedError

    @abstractmethod
    def set_instances(self, value: int) -> None:
        """Set the number of active instances of this archetype"""
        raise NotImplementedError

    @abstractmethod
    def get_max_instances(self) -> int:
        """Return the maximum instances of this prefab that may exist"""
        raise NotImplementedError


class IResidenceArchetype(IEntityArchetype):
    """Interface for archetypes that construct residences"""

    @abstractmethod
    def get_spawn_frequency(self) -> int:
        """Return the relative frequency that this prefab appears"""
        raise NotImplementedError

    @abstractmethod
    def get_zoning(self) -> ResidentialZoning:
        raise NotImplementedError


class CharacterArchetypes:
    """Collection of factories that create character entities"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, ICharacterArchetype] = {}

    def add(self, name: str, archetype: ICharacterArchetype) -> None:
        """Register a new archetype by name"""
        if name in self._registry:
            logger.debug(f"Overwrote ICharacterPrefab: ({name})")
        self._registry[name] = archetype

    def get_all(self) -> List[ICharacterArchetype]:
        """Get all stored archetypes"""
        return list(self._registry.values())

    def get(self, name: str) -> ICharacterArchetype:
        """Get an archetype by name"""
        try:
            return self._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)


class BusinessArchetypes:
    """Collection factories that create business entities"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, IBusinessArchetype] = {}

    def add(self, name: str, archetype: IBusinessArchetype) -> None:
        """Register a new archetype by name"""
        if name in self._registry:
            logger.debug(f"Overwrote Business Archetype: ({name})")
        self._registry[name] = archetype

    def get_all(self) -> List[IBusinessArchetype]:
        """Get all stored archetypes"""
        return list(self._registry.values())

    def get(self, name: str) -> IBusinessArchetype:
        """Get an archetype by name"""
        try:
            return self._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)


class ResidenceArchetypes:
    """Collection factories that create residence entities"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, IResidenceArchetype] = {}

    def add(
        self,
        name: str,
        archetype: IResidenceArchetype,
    ) -> None:
        """Register a new archetype by name"""
        if name in self._registry:
            logger.debug(f"Overwrote Residence Archetype: ({name})")
        self._registry[name] = archetype

    def get_all(self) -> List[IResidenceArchetype]:
        """Get all stored archetypes"""
        return list(self._registry.values())

    def get(self, name: str) -> IResidenceArchetype:
        """Get an archetype by name"""
        try:
            return self._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)

    def choose_random_archetype(self, rng: Random) -> Optional[IResidenceArchetype]:
        archetype_choices: List[IResidenceArchetype] = []
        archetype_weights: List[int] = []
        for archetype in self.get_all():
            archetype_choices.append(archetype)
            archetype_weights.append(archetype.get_spawn_frequency())

        if archetype_choices:
            # Choose an archetype at random
            archetype: IResidenceArchetype = rng.choices(
                population=archetype_choices, weights=archetype_weights, k=1
            )[0]

            return archetype

        return None


#########################################
#  COMPONENT FACTORIES
#########################################


class DefaultComponentFactory(IComponentFactory[Component]):
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


@dataclass(frozen=True)
class ComponentInfo:
    name: str
    component_type: Type[Component]
    factory: IComponentFactory[Component]


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
        factory: Optional[IComponentFactory[Component]] = None,
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


def choose_random_character_archetype(
    engine: NeighborlyEngine,
) -> Optional[ICharacterArchetype]:
    """Performs a weighted random selection across all character archetypes"""
    archetype_choices: List[ICharacterArchetype] = []
    archetype_weights: List[int] = []

    for archetype in engine.character_archetypes.get_all():
        archetype_choices.append(archetype)
        archetype_weights.append(archetype.get_spawn_frequency())

    if archetype_choices:
        # Choose an archetype at random
        archetype: ICharacterArchetype = engine.rng.choices(
            population=archetype_choices, weights=archetype_weights, k=1
        )[0]

        return archetype
    else:
        return None


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
