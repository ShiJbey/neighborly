"""Definition Base Types.

This module contains abstract base types of for content definitions. They are kept
separate from the default definitions to avoid circular imports and improve end-user
customization.

Definitions are factories responsible for creating certain pieces of content at runtime.

"""

from __future__ import annotations

from typing import Any, Optional

import pydantic


class DistrictDefCharacterEntry(pydantic.BaseModel):
    """Parameters for a type of character that can spawn."""

    definition_id: Optional[str] = None
    tags: list[str] = pydantic.Field(default_factory=list)

    @pydantic.root_validator()  # type: ignore
    @classmethod
    def check_id_or_tags(cls, field_values: dict[str, Any]) -> dict[str, Any]:
        """Validate the model has a definition_id or tags specified."""
        assert (
            bool(field_values["definition_id"]) is False
            and bool(field_values["tags"]) is False
        ), "Must specify definition_id or tags"

        return field_values


class DistrictDefBusinessEntry(pydantic.BaseModel):
    """Parameters for a type of business that can spawn in a district."""

    definition_id: Optional[str] = None
    tags: list[str] = pydantic.Field(default_factory=list)


class DistrictDefResidenceEntry(pydantic.BaseModel):
    """Parameters for a type of residential building that can spawn in a district."""

    definition_id: Optional[str] = None
    tags: list[str] = pydantic.Field(default_factory=list)
    characters: list[DistrictDefCharacterEntry] = pydantic.Field(default_factory=list)


class DistrictDef(pydantic.BaseModel):
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


class SkillDef(pydantic.BaseModel):
    """A definition for a skill."""

    definition_id: str
    """A unique ID for this skill, relative to the other skills."""
    display_name: str = ""
    """The skill's name."""
    description: str = ""
    """A short description of the skill."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Keywords and tags describing the skill."""


class StatModifierData(pydantic.BaseModel):
    """Configuration data for a stat modifier in a definition."""

    name: str
    value: float
    modifier_type: str = "FLAT"


class TraitDef(pydantic.BaseModel):
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
    lifespan: int
    """The number of years that this species lives."""
    can_physically_age: bool
    """Does this character go through the various life stages."""


class SettlementDefDistrictEntry(pydantic.BaseModel):
    """Settings for selecting a district."""

    definition_id: str = ""
    """The name of this definition"""
    tags: list[str] = pydantic.Field(default_factory=list)
    """A set of descriptive tags for content selection."""


class SettlementDef(pydantic.BaseModel):
    """A definition for a settlement."""

    definition_id: str
    """The name of this definition"""
    display_name: str = ""
    """The name of the settlement (overrides name_factory)."""
    name_factory: str = ""
    """The name of the factory to use to generate the settlement name."""
    districts: list[SettlementDefDistrictEntry] = pydantic.Field(default_factory=list)
    """The districts to spawn in the settlement."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Descriptive tags for this definition."""


class ResidenceDef(pydantic.BaseModel):
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
    tags: set[str] = pydantic.Field(default_factory=set)
    """Descriptive tags for this definition."""

    @property
    def is_multifamily(self) -> bool:
        """Is this a multifamily residential building"""
        return self.residential_units > 1


class CharacterDefTraitEntry(pydantic.BaseModel):
    """An entry in the traits list of a character definition."""

    trait_id: str = ""
    """The ID of the trait to add."""
    tags: list[str] = pydantic.Field(default_factory=list)
    """Tags to use to search for a trait."""


class CharacterDefStatEntry(pydantic.BaseModel):
    """An entry in the stats list of a character definition."""

    stat: str = ""
    """The name of the stat."""
    max_value: float = 999_999
    """The maximum value of the stat."""
    mix_value: float = 999_999
    """The minimum value of the stat."""
    is_discrete: bool = True
    """Round the stat value to a whole number."""
    value: Optional[int] = None
    """The value to set the skill to (overrides value_range)."""
    value_range: str = ""
    """A range to use when giving the skill a value."""


class CharacterDefSkillEntry(pydantic.BaseModel):
    """An entry in the skills list of a character definition."""

    skill_id: str = ""
    """The ID of the skill."""
    tags: list[str] = pydantic.Field(default_factory=list)
    """Tags to use to search for a skill."""
    value: Optional[int] = None
    """The value to set the skill to (overrides value_range)."""
    value_range: str = ""
    """A range to use when giving the skill a value."""


class CharacterDef(pydantic.BaseModel):
    """A definition for a character that can spawn into the world."""

    definition_id: str
    """The name of this definition."""
    first_name_factory: str
    """The factory used to generate first names for this character type."""
    last_name_factory: str
    """The factory used to generate last names for this character type."""
    sex: str
    """The sex of this character type."""
    species: list[str]
    """IDs of species to choose from and assign to the character."""
    traits: list[CharacterDefTraitEntry] = pydantic.Field(default_factory=list)
    """Default traits applied to the character during generation."""
    skills: list[CharacterDefSkillEntry] = pydantic.Field(factory=list)
    """Default skills applied to the character upon generation."""
    stats: list[CharacterDefStatEntry] = pydantic.Field(default_factory=list)
    """Default stats applied to the character during generation."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Descriptive tags for this definition."""


class JobRoleDef(pydantic.BaseModel):
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
    stat_modifiers: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Stat modifiers applied when a character takes on this role."""
    periodic_stat_boosts: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Periodic boosts repeatedly applied to stats while a character holds the role."""
    periodic_skill_boosts: list[StatModifierData] = pydantic.Field(default_factory=list)
    """Periodic boosts repeatedly applied to skills while a character holds the role."""


class BusinessDef(pydantic.BaseModel):
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
    tags: set[str] = pydantic.Field(default_factory=set)
    """Descriptive tags for this definition."""
