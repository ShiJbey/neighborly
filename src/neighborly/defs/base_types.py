"""Definition Base Types.

This module contains abstract base types of for content definitions. They are kept
separate from the default definitions to avoid circular imports and improve end-user
customization.

Definitions are factories responsible for creating certain pieces of content at runtime.

"""

from __future__ import annotations

from typing import Optional

import pydantic


class DistrictDefCharacterEntry(pydantic.BaseModel):
    """Parameters for a type of character that can spawn."""

    with_id: str = ""
    with_tags: list[str] = pydantic.Field(default_factory=list)

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


class DistrictDefBusinessEntry(pydantic.BaseModel):
    """Parameters for a type of business that can spawn in a district."""

    with_id: str = ""
    with_tags: list[str] = pydantic.Field(default_factory=list)

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


class DistrictDefResidenceEntry(pydantic.BaseModel):
    """Parameters for a type of residential building that can spawn in a district."""

    with_id: str = ""
    with_tags: list[str] = pydantic.Field(default_factory=list)
    characters: list[DistrictDefCharacterEntry] = pydantic.Field(default_factory=list)

    @pydantic.model_validator(mode="after")  # type: ignore
    def check_id_or_tags(self):
        """Validate the model has a definition_id or tags specified."""
        if bool(self.with_id) is False and bool(self.with_tags) is False:
            raise ValueError("Must specify 'with_tags' or 'with_id'")

        return self


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
    variants: list[DistrictDef] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


DistrictDef.model_rebuild()


class SkillDef(pydantic.BaseModel):
    """A definition for a skill."""

    definition_id: str
    """A unique ID for this skill, relative to the other skills."""
    display_name: str = ""
    """The skill's name."""
    description: str = ""
    """A short description of the skill."""
    variants: list[SkillDef] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


SkillDef.model_rebuild()


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
    variants: list[SkillDef] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


TraitDef.model_rebuild()


class SpeciesDef(pydantic.BaseModel):
    """A definition for a species type."""

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
    can_physically_age: bool = True
    """Does this character go through the various life stages."""
    starting_health: int = 1000
    """The amount of health points this species starts with."""
    variants: list[SpeciesDef] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


SpeciesDef.model_rebuild()


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
    variants: list[SkillDef] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


SettlementDef.model_rebuild()


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
    variants: list[ResidenceDef] = pydantic.Field(default_factory=list)
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


ResidenceDef.model_rebuild()


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


class CharacterDef(pydantic.BaseModel):
    """A definition for a character that can spawn into the world."""

    definition_id: str
    """The name of this definition."""
    first_name_factory: str = ""
    """The factory used to generate first names for this character type."""
    last_name_factory: str = ""
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
    variants: list[CharacterDef] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


CharacterDef.model_rebuild()


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
    variants: list[JobRoleDef] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


JobRoleDef.model_rebuild()


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
    employee_roles: dict[str, int] = pydantic.Field(default_factory=dict)
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
    variants: list[BusinessDef] = pydantic.Field(default_factory=list)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


BusinessDef.model_rebuild()
