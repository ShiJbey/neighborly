"""Definition Base Types.

This module contains abstract base types of for various content definitions. Each
definition is an abstract factory responsible for creating GameObjects of a given type.
Neighborly's library + abstract definition workflow leverages the abstract factory
pattern, which allows users to create new definitions, and subsequently new factory
types.

Casual users will probably not need to create their own definition types. This feature
is for people that want to:

1) Add components default to the GameObject construction process
2) Add custom fields to definitions
3) Change how existing fields are processed during construction
4) Add additional fields to the generation options

The abstract classed are kept separate from the built-in concrete definitions to
to avoid circular imports.

We chose Pydantic as the base class for all definitions to offload the data parsing and
validation processes.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import pydantic

from neighborly.ecs import GameObject, World


class ContentDefinition(pydantic.BaseModel):
    """ABC for all content definitions."""

    definition_id: str
    """The name of this definition."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


class DistrictDefCharacterEntry(pydantic.BaseModel):
    """Parameters for a type of character that can spawn."""

    with_id: str = ""
    """ID to search for when adding a character def to the spawn table."""
    with_tags: list[str] = pydantic.Field(default_factory=list)
    """Tags to search for when adding a character def to the spawn table."""
    spawn_frequency: int = 1
    """Frequency of this character def spawning relative to others."""

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


class DistrictDefBusinessEntry(pydantic.BaseModel):
    """Parameters for a type of business that can spawn in a district."""

    with_id: str = ""
    """ID to search for when adding a business to the spawn table."""
    with_tags: list[str] = pydantic.Field(default_factory=list)
    """Tags to search for when adding a business to the spawn table."""
    spawn_frequency: int = 1
    """Frequency of this business spawning relative to others."""
    max_instances: int = 999
    """Maximum number of this business that can exist at once."""
    min_population: int = 0
    """Minimum number of characters required for this business."""

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


class DistrictDefResidenceEntry(pydantic.BaseModel):
    """Parameters for a type of residential building that can spawn in a district."""

    with_id: str = ""
    """ID to search for when adding a residence def to the spawn table."""
    with_tags: list[str] = pydantic.Field(default_factory=list)
    """Tags to search for when adding a residence def to the spawn table."""
    spawn_frequency: int = 1
    """Frequency of this residence def spawning relative to others."""
    max_instances: int = 999
    """Maximum number of this residence def that can exist at once."""
    min_population: int = 0
    """Minimum number of characters required for this residence def."""

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


class DistrictGenOptions(pydantic.BaseModel):
    """Parameter overrides used when creating a new district GameObject."""

    name: str = ""
    """The name of the district."""


class DistrictDef(ContentDefinition, ABC):
    """A definition for a district within a settlement."""

    definition_id: str
    """The name of this definition."""
    name: str = ""
    """The name of the district (overrides name_factory)."""
    name_factory: str = "default"
    """The name of the factory to use to generate this district's name."""
    description: str = ""
    """A description of the district (Deprecated)."""
    business_types: list[DistrictDefBusinessEntry] = pydantic.Field(
        default_factory=list
    )
    """Settings for spawning businesses within this district type."""
    residence_types: list[DistrictDefResidenceEntry] = pydantic.Field(
        default_factory=list
    )
    """Settings for spawning residential buildings within this district type."""
    character_types: list[DistrictDefCharacterEntry] = pydantic.Field(
        default_factory=list
    )
    """Settings for spawning characters within this district type."""
    business_slots: int = 0
    """The max number of business buildings that can exist in the district."""
    residential_slots: int = 0
    """The max number of residential buildings that can exist in the district."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def instantiate(
        self,
        world: World,
        settlement: GameObject,
        options: DistrictGenOptions,
    ) -> GameObject:
        """Create instance of district using the options.

        Parameters
        ----------
        world
            The simulation's world instance.
        settlement
            The settlement the district will belong to.
        options
            Generation options.

        Returns
        -------
        GameObject
            The instantiated district.
        """

        raise NotImplementedError()


class SkillDef(ContentDefinition, ABC):
    """A definition for a skill."""

    definition_id: str
    """A unique ID for this skill, relative to the other skills."""
    name: str = ""
    """The skill's name."""
    description: str = ""
    """A short description of the skill."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def instantiate(self, world: World) -> GameObject:
        """Create a new skill using the definition's data.

        Parameters
        ----------
        world
            The simulation's World instance.

        Returns
        -------
        GameObject
            The instantiated skill.
        """

        raise NotImplementedError()


class StatModifierData(pydantic.BaseModel):
    """Configuration data for a stat modifier in a definition."""

    name: str
    value: float
    modifier_type: str = "FLAT"


class TraitDef(ContentDefinition, ABC):
    """A definition for a trait."""

    definition_id: str
    """The ID of this trait definition."""
    name: str
    """The name of this trait."""
    description: str = ""
    """A short description of the trait."""
    stat_modifiers: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Modifiers applied to the owner's stats."""
    skill_modifiers: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Modifiers applied to the owner's skills."""
    social_rules: list[str] = pydantic.Field(default_factory=list)
    """IDs of social rules to apply to the trait owner."""
    location_preferences: list[str] = pydantic.Field(default_factory=list)
    """IDs of location preference rules to apply to a character."""
    conflicts_with: set[str] = pydantic.Field(default_factory=set)
    """IDs of traits that this trait conflicts with."""
    spawn_frequency: int = 0
    """The relative frequency of this trait being chosen relative to others."""
    inheritance_chance_single: float = 0.0
    """The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float = 0.0
    """The probability of inheriting this trait if both parents have it."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def instantiate(self, world: World) -> GameObject:
        """Create a new trait using the definition's data.

        Parameters
        ----------
        world
            The simulation's World instance.

        Returns
        -------
        GameObject
            The instantiated trait.
        """

        raise NotImplementedError()


class SpeciesDef(TraitDef):
    """A definition for a species type."""

    adolescent_age: int
    """Age this species reaches adolescence."""
    young_adult_age: int
    """Age this species reaches young adulthood."""
    adult_age: int
    """Age this species reaches main adulthood."""
    senior_age: int
    """Age this species becomes a senior/elder."""
    lifespan: str
    """A range of of years that this species lives (e.g. 'MIN - MAX')."""
    can_physically_age: bool
    """Does this character go through the various life stages."""


class SettlementDefDistrictEntry(pydantic.BaseModel):
    """Settings for selecting a district."""

    with_id: str = ""
    """The name of this definition"""
    with_tags: list[str] = pydantic.Field(default_factory=list)
    """A set of descriptive tags for content selection."""

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


class SettlementGenOptions(pydantic.BaseModel):
    """Parameters used when generating new settlements."""

    name: str = ""
    """The name of the settlement."""


class SettlementDef(ContentDefinition, ABC):
    """A definition for a settlement."""

    definition_id: str
    """The name of this definition"""
    name: str = ""
    """The name of the settlement (overrides name_factory)."""
    name_factory: str = "default"
    """The name of the factory to use to generate the settlement name."""
    districts: list[SettlementDefDistrictEntry] = pydantic.Field(default_factory=list)
    """The districts to spawn in the settlement."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def instantiate(self, world: World, options: SettlementGenOptions) -> GameObject:
        """Generate a new settlement from the definition.

        Parameters
        ----------
        world
            The simulation's World instance.
        options
            The settlement to initialize.

        Returns
        -------
        GameObject
            The instantiated settlement.
        """
        raise NotImplementedError()


class ResidenceGenOptions(pydantic.BaseModel):
    """Options provided to a residence factory."""


class ResidenceDef(ContentDefinition, ABC):
    """A definition for a residential building."""

    definition_id: str
    """The name of this definition"""
    name: str
    """String displayed describing the building"""
    spawn_frequency: int = 1
    """The frequency of spawning relative to others in the district."""
    residential_units: int = 1
    """The number of individual residences in this building."""
    required_population: int = 0
    """The number of people required to build this residential building."""
    max_instances: int = 9999
    """Maximum number of this type of residential building allowed within a district."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @property
    def is_multifamily(self) -> bool:
        """Is this a multifamily residential building"""
        return self.residential_units > 1

    @abstractmethod
    def instantiate(
        self, world: World, district: GameObject, options: ResidenceGenOptions
    ) -> GameObject:
        """Create a new residential building using the definition's data.

        Parameters
        ----------
        world
            The simulation's World instance.
        district
            The district the building will belong to.

        Returns
        -------
        GameObject
            The instantiated residential building.
        """

        raise NotImplementedError()


class CharacterDefTraitEntry(pydantic.BaseModel):
    """An entry in the traits list of a character definition."""

    with_id: str = ""
    """The ID of the trait to add."""
    with_tags: list[str] = pydantic.Field(default_factory=list)
    """Tags to use to search for a trait."""

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


class CharacterDefStatEntry(pydantic.BaseModel):
    """An entry in the stats list of a character definition."""

    stat: str = ""
    """The name of the stat."""
    max_value: float = 255
    """The maximum value of the stat."""
    min_value: float = 0
    """The minimum value of the stat."""
    is_discrete: bool = True
    """Round the stat value to a whole number."""
    value: Optional[int] = None
    """The value to set the skill to (overrides value_range)."""
    value_range: str = ""
    """A range to use when giving the skill a value."""


class CharacterDefSkillEntry(pydantic.BaseModel):
    """An entry in the skills list of a character definition."""

    with_id: str = ""
    """The ID of the skill."""
    with_tags: list[str] = pydantic.Field(default_factory=list)
    """Tags to use to search for a skill."""
    value: Optional[int] = None
    """The value to set the skill to (overrides value_range)."""
    value_range: str = ""
    """A range to use when giving the skill a value."""

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


class CharacterGenOptions(pydantic.BaseModel):
    """Generation parameters for creating characters."""

    first_name: str = ""
    """The character's first name."""
    last_name: str = ""
    """The character's last name/surname/family name."""
    age: int = -1
    """The character's age (overrides life_stage)."""
    life_stage: str = ""
    """The life stage of the character."""
    traits: list[str] = pydantic.Field(default_factory=list)
    """Traits that this character should start with."""


class CharacterDef(ContentDefinition, ABC):
    """A definition for a character that can spawn into the world."""

    definition_id: str
    """The name of this definition."""
    first_name_factory: str = "default"
    """The factory used to generate first names for this character type."""
    last_name_factory: str = "default"
    """The factory used to generate last names for this character type."""
    sex: str = ""
    """The sex of this character type."""
    species: str = ""
    """IDs of species to choose from and assign to the character."""
    traits: list[CharacterDefTraitEntry] = pydantic.Field(default_factory=list)
    """Default traits applied to the character during generation."""
    skills: list[CharacterDefSkillEntry] = pydantic.Field(default_factory=list)
    """Default skills applied to the character upon generation."""
    stats: list[CharacterDefStatEntry] = pydantic.Field(default_factory=list)
    """Default stats applied to the character during generation."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def instantiate(
        self,
        world: World,
        options: CharacterGenOptions,
    ) -> GameObject:
        """Generate a new character using the definition's data.

        Parameters
        ----------
        world
            The simulation's World instance.
        options
            Generation options.

        Returns
        -------
        GameObject
            The instantiated character.
        """

        raise NotImplementedError()


class JobRoleDef(ContentDefinition, ABC):
    """A definition of a type of job characters can work at a business."""

    definition_id: str
    """The name of this definition."""
    name: str
    """The name of the role."""
    description: str = ""
    """A description of the role."""
    job_level: int = 1
    """General level of prestige associated with this role."""
    requirements: list[str] = pydantic.Field(default_factory=list)
    """Precondition query statements for this role."""
    stat_modifiers: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Stat modifiers applied when a character takes on this role."""
    periodic_stat_boosts: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Periodic boosts repeatedly applied to stats while a character holds the role."""
    periodic_skill_boosts: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Periodic boosts repeatedly applied to skills while a character holds the role."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def instantiate(self, world: World) -> GameObject:
        """Create a job role using the definition's data.

        Parameters
        ----------
        world
            The simulation's World instance.

        Returns
        -------
        GameObject
            The instantiated job role.
        """

        raise NotImplementedError()


class BusinessGenOptions(pydantic.BaseModel):
    """Parameters used to generate new businesses."""

    name: str = ""
    """The name of the business."""


class BusinessDef(ContentDefinition, ABC):
    """A definition for a business where characters can work and meet people."""

    definition_id: str
    """The name of this definition."""
    name: str = ""
    """The name for the business type (overrides name_factory)."""
    name_factory: str = "default"
    """The name of the factory used to generate names for this business type."""
    owner_role: str
    """Parameters for the business owner's job."""
    lifespan: str = "5 - 10"
    """A range of the base number of years businesses of this type last for."""
    employee_roles: dict[str, int] = pydantic.Field(default_factory=dict)
    """Parameters gor each job held by employees."""
    traits: list[str] = pydantic.Field(default_factory=list)
    """Traits this business starts with."""
    open_to_public: bool = True
    """Can this business be frequented by the general public."""
    spawn_frequency: int = 1
    """The frequency of spawning relative to others in the district."""
    min_population: int = 0
    """The minimum number of residents required to spawn the business."""
    max_instances: int = 9999
    """The maximum number of this definition that may exist in a district."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict[str, Any])
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""

    @abstractmethod
    def instantiate(
        self, world: World, district: GameObject, options: BusinessGenOptions
    ) -> GameObject:
        """Create a new business building using the definition's data.

        Parameters
        ----------
        world
            The simulation's World instance.
        district
            The district the building will belong to.
        options
            Generation options.

        Returns
        -------
        GameObject
            The instantiated business building.
        """

        raise NotImplementedError()
