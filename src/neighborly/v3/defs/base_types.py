"""Definition Base Types.

This module contains abstract base types of for content definitions. They are kept
separate from the default definitions to avoid circular imports and improve end-user
customization.

Definitions are factories responsible for creating certain pieces of content at runtime.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Optional

import pydantic

from neighborly.ecs import GameObject


class DistrictDefCharacterEntry(pydantic.BaseModel):
    """Parameters for a type of character that can spawn."""

    definition_id: Optional[str] = None
    tags: list[str] = pydantic.Field(default_factory=list)


class DistrictDefBusinessEntry(pydantic.BaseModel):
    """Parameters for a type of business that can spawn in a district."""

    definition_id: Optional[str] = None
    tags: list[str] = pydantic.Field(default_factory=list)


class DistrictDefResidenceEntry(pydantic.BaseModel):
    """Parameters for a type of residential building that can spawn in a district."""

    definition_id: Optional[str] = None
    tags: list[str] = pydantic.Field(default_factory=list)
    characters: list[DistrictDefCharacterEntry] = pydantic.Field(default_factory=list)


@pydantic.dataclass
class DistrictGenerationOptions:
    """Parameter overrides used when creating a new district GameObject."""

    definition_id: str
    """The definition to create."""
    name: Optional[str] = None
    """The name of the district."""


class DistrictDef(pydantic.BaseModel, ABC):
    """A definition for a district within a settlement."""

    definition_id: str
    """The name of this definition."""
    display_name: str = ""
    """The name of the district (overrides name_factory)."""
    name_factory: str = ""
    """The name of the factory to use to generate this district's name."""
    businesses: list[DistrictDefBusinessEntry] = pydantic.Field(default_factory=list)
    """Settings for spawning businesses within this district type."""
    residences: list[DistrictDefResidenceEntry] = pydantic.Field(default_factory=list)
    """Settings for spawning residential buildings within this district type."""
    characters: list[DistrictDefCharacterEntry] = pydantic.Field(default_factory=list)
    """Settings for spawning characters within this district type."""
    business_slots: int = 0
    """The max number of business buildings that can exist in the district."""
    residential_slots: int = 0
    """The max number of residential buildings that can exist in the district."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def initialize(
        self,
        settlement: GameObject,
        district: GameObject,
        options: DistrictGenerationOptions,
    ) -> None:
        """Initialize district's components using the definition data.

        Parameters
        ----------
        settlement
            The settlement that the district belongs to.
        district
            The district to initialize.
        options
            Initialization options.
        """
        raise NotImplementedError()


class SkillDef(pydantic.BaseModel, ABC):
    """A definition for a skill."""

    definition_id: str
    """The ID of this tag definition."""
    display_name: str
    """The name of this tag printed."""
    description: str = ""
    """A short description of the tag."""

    @abstractmethod
    def initialize(self, skill: GameObject) -> None:
        """Create a new skill using the definition's data.

        Parameters
        ----------
        skill
            The skill GameObject to initialize.
        """
        raise NotImplementedError()


class StatModifierData(pydantic.BaseModel):
    """Configuration data for a stat modifier in a definition."""

    name: str
    value: str
    modifier_type: str = "FLAT"


class TraitDef(pydantic.BaseModel, ABC):
    """A definition for a trait."""

    definition_id: str
    """The ID of this trait definition."""
    display_name: str
    """The name of this trait printed."""
    description: str = ""
    """A short description of the trait."""
    stat_modifiers: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Modifiers applied to the owner's stats."""
    skill_modifiers: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Modifiers applied to the owner's skills."""
    conflicts_with: set[str] = pydantic.Field(default_factory=set)
    """IDs of traits that this trait conflicts with."""
    spawn_frequency: int = 0
    """The relative frequency of this trait being chosen relative to others."""
    inheritance_chance_single: float = 0.0
    """The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float = 0.0
    """The probability of inheriting this trait if both parents have it."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def initialize(self, trait: GameObject) -> None:
        """Create a new trait using the definition's data.

        Parameters
        ----------
        trait
            The trait to initialize.
        """
        raise NotImplementedError()


class SettlementDefDistrictEntry(pydantic.BaseModel):
    """Settings for selecting a district."""

    definition_id: str = ""
    """The name of this definition"""
    tags: list[str] = pydantic.Field(default_factory=list)
    """A set of descriptive tags for content selection."""


@pydantic.dataclass
class SettlementGenerationOptions:
    """Parameters used when generating new settlements."""

    definition_id: str
    """The definition to generate."""
    name: str = ""
    """The name of the settlement."""


class SettlementDef(pydantic.BaseModel, ABC):
    """A definition for a settlement."""

    definition_id: str
    """The name of this definition"""
    display_name: str = ""
    """The name of the settlement (overrides name_factory)."""
    name_factory: str = ""
    """The name of the factory to use to generate the settlement name."""
    districts: list[SettlementDefDistrictEntry] = pydantic.Field(default_factory=list)
    """The districts to spawn in the settlement."""

    @abstractmethod
    def initialize(
        self, settlement: GameObject, options: SettlementGenerationOptions
    ) -> None:
        """Initialize a settlements components using the definition data.

        Parameters
        ----------
        settlement
            The settlement to initialize.
        options
            Initialization options.
        """
        raise NotImplementedError()


class ResidenceDef(pydantic.BaseModel, ABC):
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


@pydantic.dataclass
class CharacterGenerationOptions:
    """Generation parameters for creating characters."""

    definition_id: str
    """The definition to use for generation."""
    first_name: str = ""
    """The character's first name."""
    last_name: str = ""
    """The character's last name/surname/family name."""
    sex: str = ""
    """The character's biological sex."""
    age: int = -1
    """The character's age."""


class CharacterDef(pydantic.BaseModel, ABC):
    """A definition for a character that can spawn into the world."""

    MAX_STARTING_TRAITS: ClassVar[int] = 3
    """Maximum number of traits a character can spawn with."""
    MAX_STARTING_SKILLS: ClassVar[int] = 3
    """Maximum number of skills a character can spawn with."""

    definition_id: str
    """The name of this definition."""
    name_factory: str
    """The name of the factory used to generate names for characters."""
    spawn_frequency: int = 1
    """The frequency of spawning relative to others in the district."""
    species: list[str]
    """IDs of species to choose from and assign to the character."""
    default_traits: list[str] = pydantic.Field(default_factory=list)
    """Default traits applied to the character during generation."""
    default_skills: dict[str, tuple[int, int]] = pydantic.Field(factory=dict)
    """Default skills applied to the character upon generation."""

    @abstractmethod
    def initialize(
        self, character: GameObject, options: CharacterGenerationOptions
    ) -> None:
        """Initialize a character's components using the definition data.

        Parameters
        ----------
        character
            The character to initialize.
        options
            Initialization options.
        """
        raise NotImplementedError()


class JobRoleDef(pydantic.BaseModel, ABC):
    """A definition of a type of job characters can work at a business."""

    definition_id: str
    """The name of this definition."""
    display_name: str
    """The name of the role."""
    description: str = ""
    """A description of the role."""
    job_level: int = 1
    """General level of prestige associated with this role."""
    requirements: list[str] = pydantic.Field(default_factory=list)
    """Precondition query statements for this role."""
    effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Effects applied when the taking on the role."""
    skill_growth: list[StatModifierData] = pydantic.Field(factory=list)
    """Modifiers repeatedly to base skill stats as someone hold the job."""

    @abstractmethod
    def initialize(self, role: GameObject) -> None:
        """Initialize a job roles' components using the definition data.

        Parameters
        ----------
        role
            The role to initialize.
        """
        raise NotImplementedError()


@pydantic.dataclass
class BusinessGenerationOptions:
    """Parameters used to generate new businesses."""

    definition_id: str
    """The definition to generate."""
    name: str = ""
    """The name of the business."""


class BusinessDef(pydantic.BaseModel, ABC):
    """A definition for a business where characters can work and meet people."""

    definition_id: str
    """The name of this definition"""
    display_name: str = ""
    """The name for the business type (overrides name_factory)."""
    name_factory: str = ""
    """The name of the factory used to generate names for this business type."""
    owner_role: str
    """Parameters for the business owner's job."""
    employee_roles: dict[str, int] = pydantic.Field(factory=dict)
    """Parameters gor each job held by employees."""
    traits: list[str] = pydantic.Field(default_factory=list)
    """Descriptive tags for this business type."""
    open_to_public: bool = True
    """Can this business be frequented by the general public."""
    spawn_frequency: int = 1
    """The frequency of spawning relative to others in the district"""
    min_population: int = 0
    """The minimum number of residents required to spawn the business."""
    max_instances: int = 9999
    """The maximum number of this definition that may exist in a district."""

    @abstractmethod
    def initialize(
        self,
        district: GameObject,
        business: GameObject,
        options: BusinessGenerationOptions,
    ) -> None:
        """Initialize a business' components using the definition data.

        Parameters
        ----------
        district
            The district where the business resides.
        business
            The business to initialize.
        options
            Initialization options.
        """
        raise NotImplementedError()
