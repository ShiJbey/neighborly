from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Set, Type

from neighborly.builtin.components import Active, Age, Lifespan, LifeStages, Name
from neighborly.core.business import (
    Business,
    IBusinessType,
    Services,
    ServiceType,
    ServiceTypes,
    WorkHistory,
    parse_operating_hour_str,
)
from neighborly.core.character import CharacterName, GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationships
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine

logger = logging.getLogger(__name__)


class CharacterArchetypes:
    """Static class that manages factories that create character archetypes"""

    _registry: Dict[str, ICharacterArchetype] = {}

    @classmethod
    def add(cls, name: str, archetype: ICharacterArchetype) -> None:
        """Register a new archetype by name"""
        if name in cls._registry:
            logger.debug(f"Overwrote ICharacterPrefab: ({name})")
        cls._registry[name] = archetype

    @classmethod
    def get_all(cls) -> List[ICharacterArchetype]:
        """Get all stored archetypes"""
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> ICharacterArchetype:
        """Get an archetype by name"""
        try:
            return cls._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)


class BusinessArchetypes:
    """Static class that manages factories that create business archetypes"""

    _registry: Dict[str, IBusinessArchetype] = {}

    @classmethod
    def add(cls, name: str, archetype: IBusinessArchetype) -> None:
        """Register a new archetype by name"""
        if name in cls._registry:
            logger.debug(f"Overwrote Business Archetype: ({name})")
        cls._registry[name] = archetype

    @classmethod
    def get_all(cls) -> List[IBusinessArchetype]:
        """Get all stored archetypes"""
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> IBusinessArchetype:
        """Get an archetype by name"""
        try:
            return cls._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)


class ResidenceArchetypes:
    _registry: Dict[str, IResidenceArchetype] = {}

    @classmethod
    def add(
        cls,
        name: str,
        archetype: IResidenceArchetype,
    ) -> None:
        """Register a new archetype by name"""
        if name in cls._registry:
            logger.debug(f"Overwrote Residence Archetype: ({name})")
        cls._registry[name] = archetype

    @classmethod
    def get_all(cls) -> List[IResidenceArchetype]:
        """Get all stored archetypes"""
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> IResidenceArchetype:
        """Get an archetype by name"""
        try:
            return cls._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)


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
    def get_spawn_frequency(self) -> int:
        """Return the relative frequency that this prefab appears"""
        raise NotImplementedError

    @abstractmethod
    def create(self, world: World, **kwargs) -> GameObject:
        """Create a new instance of this prefab"""
        raise NotImplementedError


class ICharacterArchetype(IEntityArchetype):
    """Interface for archetypes that construct characters"""

    @abstractmethod
    def get_max_children_at_spawn(self) -> int:
        """Return the maximum amount of children this prefab can have when spawning"""
        raise NotImplementedError

    @abstractmethod
    def get_chance_spawn_with_spouse(self) -> float:
        """Return the chance that a character from this prefab spawns with a spouse"""
        raise NotImplementedError


class BaseCharacterArchetype(ICharacterArchetype):
    """Base factory class for constructing new characters"""

    __slots__ = (
        "spawn_frequency",
        "chance_spawn_with_spouse",
        "max_children_at_spawn",
    )

    def __init__(
        self,
        spawn_frequency: int = 1,
        chance_spawn_with_spouse: float = 0.5,
        max_children_at_spawn: int = 0,
    ) -> None:
        self.spawn_frequency: int = spawn_frequency
        self.max_children_at_spawn: int = max_children_at_spawn
        self.chance_spawn_with_spouse: float = chance_spawn_with_spouse

    def get_spawn_frequency(self) -> int:
        return self.spawn_frequency

    def get_max_children_at_spawn(self) -> int:
        """Return the maximum amount of children this prefab can have when spawning"""
        return self.max_children_at_spawn

    def get_chance_spawn_with_spouse(self) -> float:
        """Return the chance that a character from this prefab spawns with a spouse"""
        return self.chance_spawn_with_spouse

    def create(self, world: World, **kwargs) -> GameObject:
        # Perform calculations first and return the base character GameObject
        return world.spawn_gameobject(
            [
                Active(),
                GameCharacter(),
                Routine(),
                Age(),
                CharacterName("First", "Last"),
                WorkHistory(),
                LifeStages(
                    {
                        "child": 0,
                        "teen": 13,
                        "young_adult": 18,
                        "adult": 30,
                        "elder": 65,
                    }
                ),
                PersonalValues.create(world),
                Relationships(),
            ]
        )


class IBusinessArchetype(IEntityArchetype):
    """Interface for archetypes that construct businesses"""

    @abstractmethod
    def get_business_type(self) -> Type[IBusinessType]:
        """Get the IBusiness Type that the archetype constructs"""
        raise NotImplementedError

    @abstractmethod
    def get_min_population(self) -> int:
        """Return the minimum population needed for this business to be constructed"""
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


class BaseBusinessArchetype(IBusinessArchetype):
    """
    Shared information about all businesses that
    have this type
    """

    __slots__ = (
        "business_type",
        "hours",
        "name_format",
        "owner_type",
        "max_instances",
        "min_population",
        "employee_types",
        "services",
        "spawn_frequency",
        "year_available",
        "year_obsolete",
        "instances",
    )

    def __init__(
        self,
        business_type: Type[IBusinessType],
        name_format: str,
        hours: str = "day",
        owner_type: Optional[str] = None,
        max_instances: int = 9999,
        min_population: int = 0,
        employee_types: Optional[Dict[str, int]] = None,
        services: Optional[List[str]] = None,
        spawn_frequency: int = 1,
        year_available: int = -1,
        year_obsolete: int = 9999,
        average_lifespan: int = 20,
    ) -> None:
        self.business_type: Type[IBusinessType] = business_type
        self.hours: str = hours
        self.name_format: str = name_format
        self.owner_type: Optional[str] = owner_type
        self.max_instances: int = max_instances
        self.min_population: int = min_population
        self.employee_types: Dict[str, int] = employee_types if employee_types else {}
        self.services: List[str] = services if services else []
        self.spawn_frequency: int = spawn_frequency
        self.year_available: int = year_available
        self.year_obsolete: int = year_obsolete
        self.instances: int = 0
        self.average_lifespan: int = average_lifespan

    def get_spawn_frequency(self) -> int:
        """Return the relative frequency that this prefab appears"""
        return self.spawn_frequency

    def get_min_population(self) -> int:
        """Return the minimum population needed for this business to be constructed"""
        return self.min_population

    def get_year_available(self) -> int:
        """Return the year that this business is available to construct"""
        return self.year_available

    def get_year_obsolete(self) -> int:
        """Return the year that this business is no longer available to construct"""
        return self.year_obsolete

    def get_business_type(self) -> Type[IBusinessType]:
        return self.business_type

    def get_instances(self) -> int:
        return self.instances

    def set_instances(self, value: int) -> None:
        self.instances = value

    def get_max_instances(self) -> int:
        return self.max_instances

    def create(self, world: World, **kwargs) -> GameObject:
        engine = world.get_resource(NeighborlyEngine)

        services: Set[ServiceType] = set()

        for service in self.services:
            services.add(ServiceTypes.get(service))

        return world.spawn_gameobject(
            [
                self.business_type(),
                Business(
                    operating_hours=parse_operating_hour_str(self.hours),
                    owner_type=self.owner_type,
                    open_positions=self.employee_types,
                ),
                Age(0),
                Services(services),
                Name(engine.name_generator.get_name(self.name_format)),
                Position2D(),
                Location(),
                Lifespan(self.average_lifespan),
            ]
        )


class ResidentialZoning(Enum):
    SingleFamily = 0
    MultiFamily = 0


class IResidenceArchetype(IEntityArchetype):
    """Interface for archetypes that construct residences"""

    @abstractmethod
    def get_zoning(self) -> ResidentialZoning:
        raise NotImplementedError


class BaseResidenceArchetype(IResidenceArchetype):
    __slots__ = ("spawn_frequency", "zoning")

    def __init__(
        self,
        zoning: ResidentialZoning = ResidentialZoning.SingleFamily,
        spawn_frequency: int = 1,
    ) -> None:
        self.spawn_frequency: int = spawn_frequency
        self.zoning: ResidentialZoning = zoning

    def get_spawn_frequency(self) -> int:
        return self.spawn_frequency

    def get_zoning(self) -> ResidentialZoning:
        return self.zoning

    def create(self, world: World, **kwargs) -> GameObject:
        return world.spawn_gameobject([Residence(), Location(), Position2D()])


class ArchetypeRef(Component):

    __slots__ = "name"

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"
