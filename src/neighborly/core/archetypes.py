from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from neighborly.builtin.components import Active, Age, CanGetPregnant, Name
from neighborly.core.business import Business, Services, WorkHistory, logger
from neighborly.core.character import GameCharacter, LifeStageAges
from neighborly.core.ecs import Component, EntityArchetype, GameObject, World
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine


def spawns_character(name: str, spawn_frequency: int = 1):
    def decorator(fn):
        ...

    return decorator


@spawns_character("Human")
def create_human(world: World) -> None:
    ...


class Prefab(ABC):
    """A specification for a hierarchy of GameObjects"""

    @abstractmethod
    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError


class CharacterPrefab(Prefab):
    __slots__ = (
        "name_format",
        "spawn_multiplier",
        "chance_spawn_with_spouse",
        "max_children_at_spawn",
        "archetype",
    )

    def __init__(
        self,
        name_format: str = "#first_name# #family_name#",
        spawn_multiplier: int = 1,
        chance_spawn_with_spouse: float = 0.5,
        max_children_at_spawn: int = 0,
        extra_components: Optional[Dict[Type[Component], Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(name)
        self.name_format: str = name_format
        self.spawn_multiplier: int = spawn_multiplier
        self.chance_spawn_with_spouse: float = chance_spawn_with_spouse
        self.max_children_at_spawn: int = max_children_at_spawn
        self.archetype = EntityArchetype("")

        self.archetype.add(GameCharacter)
        self.archetype.add(Routine, presets="default")
        self.archetype.add(PersonalValues)
        self.archetype.add(WorkHistory)
        self.archetype.add(Age)
        self.archetype.add(CanGetPregnant)

        if extra_components:
            for component_type, params in extra_components.items():
                self.archetype.add(component_type, **params)

    def instantiate(self, world: World) -> GameObject:
        return world.spawn_archetype(self.archetype)


class CharacterArchetype(EntityArchetype):
    """
    Archetype subclass for building characters
    """

    __slots__ = (
        "name_format",
        "spawn_multiplier",
        "chance_spawn_with_spouse",
        "max_children_at_spawn",
    )

    def __init__(
        self,
        name: str,
        name_format: str = "#first_name# #family_name#",
        spawn_multiplier: int = 1,
        chance_spawn_with_spouse: float = 0.5,
        max_children_at_spawn: int = 0,
        extra_components: Optional[Dict[Type[Component], Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(name)
        self.name_format: str = name_format
        self.spawn_multiplier: int = spawn_multiplier
        self.chance_spawn_with_spouse: float = chance_spawn_with_spouse
        self.max_children_at_spawn: int = max_children_at_spawn

        self.add(GameCharacter)
        self.add(Routine, presets="default")
        self.add(PersonalValues)
        self.add(WorkHistory)
        self.add(Age)
        self.add(CanGetPregnant)

        if extra_components:
            for component_type, params in extra_components.items():
                self.add(component_type, **params)


class CharacterArchetypeLibrary:
    _registry: Dict[str, CharacterArchetype] = {}

    @classmethod
    def add(cls, archetype: CharacterArchetype, name: Optional[str] = None) -> None:
        """Register a new LifeEventType mapped to a name"""
        entry_key = name if name else archetype.name
        if entry_key in cls._registry:
            logger.debug(f"Overwrote CharacterArchetype: ({entry_key})")
        cls._registry[entry_key] = archetype

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
        "spawn_multiplier",
        "year_available",
        "year_obsolete",
    )

    def __init__(
        self,
        name: str,
        hours: Optional[str] = None,
        name_format: Optional[str] = None,
        owner_type: Optional[str] = None,
        max_instances: int = 9999,
        min_population: int = 0,
        employee_types: Optional[Dict[str, int]] = None,
        services: Optional[List[str]] = None,
        spawn_multiplier: int = 1,
        extra_components: Optional[Dict[Type[Component], Dict[str, Any]]] = None,
        year_available: int = -1,
        year_obsolete: int = 9999,
    ) -> None:
        super().__init__(name)
        self.hours: str = hours if hours else "day"
        self.name_format: str = name_format if name_format else name
        self.owner_type: Optional[str] = owner_type
        self.max_instances: int = max_instances
        self.min_population: int = min_population
        self.employee_types: Dict[str, int] = employee_types if employee_types else {}
        self.services: List[str] = services if services else []
        self.spawn_multiplier: int = spawn_multiplier
        self.year_available: int = year_available
        self.year_obsolete: int = year_obsolete

        self.add(
            Business,
            name_format=self.name_format,
            hours=self.hours,
            owner_type=self.owner_type,
            employee_types=self.employee_types,
        )
        self.add(Location)
        self.add(Position2D)
        self.add(Name, name=self.name)
        self.add(Age)
        self.add(Services, services=services)

        if extra_components:
            for component_type, params in extra_components.items():
                self.add(component_type, **params)


class BusinessArchetypeLibrary:
    _registry: Dict[str, BusinessArchetype] = {}

    @classmethod
    def add(cls, archetype: BusinessArchetype, name: Optional[str] = None) -> None:
        """Register a new LifeEventType mapped to a name"""
        entry_key = name if name else archetype.name
        if entry_key in cls._registry:
            logger.debug(f"Overwrote BusinessArchetype: ({entry_key})")
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
        extra_components: Optional[Dict[Type[Component], Dict[str, Any]]] = None,
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
        name: Optional[str] = None,
    ) -> None:
        """Register a new LifeEventType mapped to a name"""
        entry_key = name if name else archetype.name
        if entry_key in cls._registry:
            logger.debug(f"Overwrote ResidenceArchetype: ({entry_key})")
        cls._registry[entry_key] = archetype

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
