from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from random import Random
from typing import Any, Dict, List, Optional, Type

from neighborly.core.business import IBusinessType
from neighborly.core.ecs import GameObject, World

logger = logging.getLogger(__name__)


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
    def get_spawn_frequency(self) -> int:
        """Return the relative frequency that this prefab appears"""
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
    def get_chance_spawn_with_spouse(self) -> float:
        """Return the chance that a character from this prefab spawns with a spouse"""
        raise NotImplementedError


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


class ResidentialZoning(Enum):
    SingleFamily = 0
    MultiFamily = 0


class IResidenceArchetype(IEntityArchetype):
    """Interface for archetypes that construct residences"""

    @abstractmethod
    def get_zoning(self) -> ResidentialZoning:
        raise NotImplementedError
