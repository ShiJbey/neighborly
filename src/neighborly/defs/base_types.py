"""Definition Base Types.

This module contains abstract base types of for content definitions. They are kept
separate from the default definitions to avoid circular imports and improve end-user
customization.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import attrs

from neighborly.ecs import GameObject


@attrs.define(kw_only=True)
class DistrictDef(ABC):
    """A definition for a district type specified by the user."""

    definition_id: str
    """The name of this definition."""
    display_name: str
    """A function that generates a name for the district."""
    description: str = ""
    """A function that generates a description for the district."""
    business_types: list[dict[str, Any]] = attrs.field(factory=dict[str, Any])
    """A function that generates business types for the district."""
    residence_types: list[dict[str, Any]] = attrs.field(factory=dict[str, Any])
    """A function that generates residence types for the district."""
    character_types: list[dict[str, Any]] = attrs.field(factory=dict[str, Any])
    """A function that generates character types for the district."""
    business_slots: int = 0
    """The max number of business buildings that can exist in the district."""
    residential_slots: int = 0
    """The max number of residential buildings that can exist in the district."""

    @abstractmethod
    def initialize(self, settlement: GameObject, district: GameObject) -> None:
        """Initialize district's components using the definition data.

        Parameters
        ----------
        settlement
            The settlement that the district belongs to
        district
            The district to initialize
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_obj(cls, obj: dict[str, Any]) -> DistrictDef:
        """Create a district definition from a data dictionary.

        Parameters
        ----------
        obj
            A dictionary of configuration settings.

        Returns
        -------
        DistrictDef
            An instance of this district definition
        """
        raise NotImplementedError()


@attrs.define(kw_only=True)
class SkillDef(ABC):
    """A definition for a skill type."""

    definition_id: str
    """The ID of this tag definition."""
    display_name: str
    """The name of this tag printed."""
    description: str = ""
    """A short description of the tag."""

    @classmethod
    @abstractmethod
    def from_obj(cls, obj: dict[str, Any]) -> SkillDef:
        """Create a tag definition from a raw data.

        Parameters
        ----------
        obj
            A data dictionary.

        Returns
        -------
        TraitDef
            An instantiated skill definition.
        """
        raise NotImplementedError()

    @abstractmethod
    def initialize(self, skill: GameObject) -> None:
        """Create a new skill using the definition's data.

        Parameters
        ----------
        skill
            The skill GameObject to initialize.
        """
        raise NotImplementedError()


@attrs.define(kw_only=True)
class TraitDef(ABC):
    """A definition for a trait type."""

    definition_id: str
    """The ID of this trait definition."""
    display_name: str
    """The name of this trait printed."""
    description: str = ""
    """A short description of the trait."""
    effects: list[dict[str, Any]] = attrs.field(factory=dict[str, Any])
    """Effects applied when a GameObject gains this trait."""
    conflicts_with: frozenset[str] = attrs.field(factory=frozenset)
    """IDs of traits that this trait conflicts with."""
    spawn_frequency: int = 0
    """The relative frequency of this trait being chosen relative to others."""
    inheritance_chance_single: float = 0.0
    """The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float = 0.0
    """The probability of inheriting this trait if both parents have it."""

    @classmethod
    @abstractmethod
    def from_obj(cls, obj: dict[str, Any]) -> TraitDef:
        """Create a trait definition from a raw data.

        Parameters
        ----------
        obj
            A data dictionary.

        Returns
        -------
        TraitDef
            An instantiated trait definition.
        """
        raise NotImplementedError()

    @abstractmethod
    def initialize(self, trait: GameObject) -> None:
        """Create a new trait using the definition's data.

        Parameters
        ----------
        trait
            The trait to initialize.
        """
        raise NotImplementedError()


@attrs.define(kw_only=True)
class SettlementDef(ABC):
    """A definition for a settlement type specified by the user."""

    definition_id: str
    """The name of this definition"""
    display_name: str
    """The name of the settlement for use in GUI's and descriptions."""
    districts: list[str] = attrs.field(factory=list[str])
    """A function that generates the types of districts that exist in the settlement."""

    @abstractmethod
    def initialize(self, settlement: GameObject) -> None:
        """Initialize a settlements components using the definition data.

        Parameters
        ----------
        settlement
            The settlement to initialize.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_obj(cls, obj: dict[str, Any]) -> SettlementDef:
        """Create a settlement definition from a data dictionary.

        Parameters
        ----------
        obj
            A dictionary of configuration settings.

        Returns
        -------
        SettlementDef
            An instance of this definition.
        """
        raise NotImplementedError()


@attrs.define(kw_only=True)
class ResidenceDef(ABC):
    """A definition for a residential building."""

    definition_id: str
    """The name of this definition"""
    display_name: str
    """String displayed describing the building"""
    spawn_frequency: int = 1
    """The frequency of spawning relative to others in the district."""
    residential_units: int = 1
    """The number of individual residences in this building."""
    required_population: int = 0
    """The number of people required to build this residential building."""
    max_instances: int = 9999
    """Maximum number of this type of residential building allowed within a district."""

    @property
    def is_multifamily(self) -> bool:
        """Is this a multifamily residential building"""
        return self.residential_units > 1

    @abstractmethod
    def initialize(self, district: GameObject, residence: GameObject) -> None:
        """Initialize the components for a residence.

        Parameters
        ----------
        district
            The district that the residence belongs to
        residence
            The residential building.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_obj(cls, obj: dict[str, Any]) -> ResidenceDef:
        """Create a residence definition from a data dictionary.

        Parameters
        ----------
        obj
            A dictionary of configuration settings.

        Returns
        -------
        ResidenceDef
            An instance of this definition.
        """
        raise NotImplementedError()


@attrs.define(kw_only=True)
class CharacterDef(ABC):
    """A definition for a character that can spawn into the world."""

    definition_id: str
    """The name of this definition."""
    spawn_frequency: int = 1
    """The frequency of spawning relative to others in the district."""
    species: list[str]
    """IDs of species to choose from and assign to the character."""
    max_traits: int = 5
    """The max number of traits this character type spawns with."""
    default_traits: list[str] = attrs.field(factory=list[str])
    """Default traits applied to the character during generation."""
    default_skills: list[dict[str, Any]] = attrs.field(factory=list[dict[str, Any]])
    """Default skills applied to the character upon generation."""

    @abstractmethod
    def initialize(self, character: GameObject, **kwargs: Any) -> None:
        """Initialize a character's components using the definition data.

        Parameters
        ----------
        character
            The character to initialize.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_obj(cls, obj: dict[str, Any]) -> CharacterDef:
        """Create a character definition from a data dictionary.

        Parameters
        ----------
        obj
            A dictionary of configuration settings.

        Returns
        -------
        CharacterDef
            An instance of this definition.
        """
        raise NotImplementedError()


@attrs.define(kw_only=True)
class JobRoleDef(ABC):
    """A definition of a type of job characters can work at a business."""

    definition_id: str
    """The name of this definition."""
    display_name: str
    """The name of the role."""
    job_level: int
    """General level of prestige associated with this role."""
    requirements: list[dict[str, Any]] = attrs.field(factory=list[dict[str, Any]])
    """Requirement functions for the role."""
    effects: list[dict[str, Any]] = attrs.field(factory=list[dict[str, Any]])
    """Effects applied when the taking on the role."""
    monthly_effects: list[dict[str, Any]] = attrs.field(factory=list[dict[str, Any]])
    """Effects applied every month the character has the role."""

    @classmethod
    @abstractmethod
    def from_obj(cls, obj: dict[str, Any]) -> JobRoleDef:
        """Create JobRoleDef from a data dictionary.

        Parameters
        ----------
        obj
            A dictionary of configuration settings.

        Returns
        -------
        JobRoleDef
            An instance of this job role definition.
        """
        raise NotImplementedError()

    @abstractmethod
    def initialize(self, role: GameObject, **kwargs: Any) -> None:
        """Initialize a job roles' components using the definition data.

        Parameters
        ----------
        role
            The role to initialize.
        """
        raise NotImplementedError()


@attrs.define(kw_only=True)
class BusinessDef(ABC):
    """A definition for a business where characters can work and meet people."""

    definition_id: str
    """The name of this definition"""
    display_name: str
    """A function that generates a name for the business."""
    owner_role: str
    """Parameters for the business owner's job."""
    employee_roles: dict[str, int] = attrs.field(factory=dict[str, int])
    """Parameters gor each job held by employees."""
    traits: list[str] = attrs.field(factory=list[str])
    """Descriptive tags for this business type."""
    open_to_public: bool = True
    """Can this business be frequented by the general public."""
    spawn_frequency: int = 1
    """The frequency of spawning relative to others in the district"""
    min_population: int = 0
    """The minimum number of residents required to spawn the business."""
    max_instances: int = 9999
    """The maximum number of this definition that may exist in a district."""

    def initialize(self, district: GameObject, business: GameObject) -> None:
        """Initialize a business' components using the definition data.

        Parameters
        ----------
        district
            The district where the business resides.
        business
            The business to initialize.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_obj(cls, obj: dict[str, Any]) -> BusinessDef:
        """Create a business definition from a data dictionary

        Parameters
        ----------
        obj
            A dictionary of configuration settings.

        Returns
        -------
        BusinessDef
            An instance of this business definition
        """
        raise NotImplementedError()
