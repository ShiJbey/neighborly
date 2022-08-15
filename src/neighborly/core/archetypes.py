from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from neighborly.core.business import Business, BusinessService, logger
from neighborly.core.character import GameCharacter, LifeStages
from neighborly.core.ecs import Component, EntityArchetype
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine


class CharacterArchetype(EntityArchetype):
    """
    Archetype subclass for building characters
    """

    __slots__ = "name_format", "spawn_multiplier"

    def __init__(
        self,
        name: str,
        lifespan: int,
        life_stages: LifeStages,
        name_format: str = "#first_name# #family_name#",
        chance_can_get_pregnant: float = 0.5,
        spawn_multiplier: int = 1,
        extra_components: Dict[Type[Component], Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name)
        self.name_format: str = name_format
        self.spawn_multiplier: int = spawn_multiplier

        self.add(
            GameCharacter,
            character_type=name,
            name_format=name_format,
            lifespan=lifespan,
            life_stages=life_stages,
            chance_can_get_pregnant=chance_can_get_pregnant,
        )

        self.add(Routine)
        self.add(PersonalValues)

        if extra_components:
            for component_type, params in extra_components.items():
                self.add(component_type, **params)


class CharacterArchetypeLibrary:
    _registry: Dict[str, CharacterArchetype] = {}

    @classmethod
    def add(cls, archetype: CharacterArchetype, name: Optional[str] = None) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name if name else archetype.name] = archetype

    @classmethod
    def get_all(cls) -> List[CharacterArchetype]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> CharacterArchetype:
        """Get a LifeEventType using a name"""
        try:
            return cls._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)


class BusinessArchetype(EntityArchetype):
    """
    Shared information about all businesses that
    have this type
    """

    __slots__ = (
        "hours",
        "name_format",
        "owner_type",
        "max_instances",
        "min_population",
        "employee_types",
        "services",
        "service_flags",
        "spawn_multiplier",
        "year_available",
        "year_obsolete",
    )

    def __init__(
        self,
        name: str,
        hours: List[str] = None,
        name_format: str = None,
        owner_type: str = None,
        max_instances: int = 9999,
        min_population: int = 0,
        employee_types: Dict[str, int] = None,
        services: List[str] = None,
        spawn_multiplier: int = 1,
        extra_components: Dict[Type[Component], Dict[str, Any]] = None,
        year_available: int = -1,
        year_obsolete: int = 9999,
    ) -> None:
        super().__init__(name)
        self.hours: List[str] = hours if hours else ["day"]
        self.name_format: str = name_format if name_format else name
        self.owner_type: Optional[str] = owner_type
        self.max_instances: int = max_instances
        self.min_population: int = min_population
        self.employee_types: Dict[str, int] = employee_types if employee_types else {}
        self.services: List[str] = services if services else {}
        self.service_flags: BusinessService = BusinessService.NONE
        self.spawn_multiplier: int = spawn_multiplier
        for service_name in self.services:
            self.service_flags |= BusinessService[
                service_name.strip().upper().replace(" ", "_")
            ]
        self.year_available: int = year_available
        self.year_obsolete: int = year_obsolete

        self.add(
            Business,
            business_type=self.name,
            name_format=self.name_format,
            hours=self.hours,
            owner_type=self.owner_type,
            employee_types=self.employee_types,
            services=self.service_flags,
        )
        self.add(Location)
        self.add(Position2D)

        if extra_components:
            for component_type, params in extra_components.items():
                self.add(component_type, **params)


class BusinessArchetypeLibrary:
    _registry: Dict[str, BusinessArchetype] = {}

    @classmethod
    def add(
        cls, archetype: BusinessArchetype, name: str = None, overwrite_ok: bool = False
    ) -> None:
        """Register a new LifeEventType mapped to a name"""
        entry_key = name if name else archetype.name
        if entry_key in cls._registry and not overwrite_ok:
            logger.warning(f"Attempted to overwrite BusinessArchetype: ({entry_key})")
            return
        cls._registry[entry_key] = archetype

    @classmethod
    def get_all(cls) -> List[BusinessArchetype]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> BusinessArchetype:
        """Get a LifeEventType using a name"""
        try:
            return cls._registry[name]
        except KeyError:
            raise ArchetypeNotFoundError(name)


class ResidenceArchetype(EntityArchetype):
    __slots__ = ("spawn_multiplier",)

    def __init__(
        self,
        name: str,
        spawn_multiplier: int = 1,
        extra_components: Dict[Type[Component], Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name)
        self.spawn_multiplier: int = spawn_multiplier

        self.add(Residence)
        self.add(Location)
        self.add(Position2D)

        if extra_components:
            for component_type, params in extra_components.items():
                self.add(component_type, **params)


class ResidenceArchetypeLibrary:
    _registry: Dict[str, ResidenceArchetype] = {}

    @classmethod
    def add(
        cls,
        archetype: ResidenceArchetype,
        name: str = None,
    ) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name if name else archetype.name] = archetype

    @classmethod
    def get_all(cls) -> List[ResidenceArchetype]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> ResidenceArchetype:
        """Get a LifeEventType using a name"""
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
