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

The abstract classed are kept separate from the built-in concrete definitions
to avoid circular imports.

We chose Pydantic as the base class for all definitions to offload the data parsing and
validation processes.

"""

from __future__ import annotations

from typing import Any, Optional

import pydantic


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


class DistrictDef(ContentDefinition):
    """A definition for a district within a settlement."""

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
    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""


class SkillDef(ContentDefinition):
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


class TraitDef(ContentDefinition):
    """A definition for a trait."""

    definition_id: str
    """The ID of this trait definition."""
    name: str
    """The name of this trait."""
    trait_type: str
    """The kind of GameObject the trait can attach to."""
    description: str = ""
    """A short description of the trait."""
    effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Effects applied when a GameObject has this trait."""
    incoming_relationship_effects: list[dict[str, Any]] = pydantic.Field(
        default_factory=list
    )
    """(Agents only) Effects to incoming relationships."""
    outgoing_relationship_effects: list[dict[str, Any]] = pydantic.Field(
        default_factory=list
    )
    """(Agents only) Effects to outgoing relationships."""
    owner_effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """(Relationships only) Effects to the owner of a relationship."""
    target_effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """(Relationships only) Effects to the target of a relationship."""
    conflicts_with: set[str] = pydantic.Field(default_factory=set)
    """IDs of traits that this trait conflicts with."""
    spawn_frequency: int = 0
    """(Agents only) The relative frequency of an agent spawning with this trait."""
    is_inheritable: bool = False
    """(Agents only) Is the trait inheritable."""
    inheritance_chance_single: float = 0.0
    """(Agents only) The probability of inheriting this trait if one parent has it."""
    inheritance_chance_both: float = 0.0
    """(Agents only) The probability of inheriting this trait if both parents have it."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


class SpeciesDef(ContentDefinition):
    """A definition for a species type."""

    definition_id: str
    """The ID of this species definition."""
    name: str
    """The name of this species."""
    description: str = ""
    """A short description of the trait."""
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
    can_physically_age: bool = True
    """Does this character go through the various life stages."""
    traits: list[str] = pydantic.Field(default_factory=list)
    """Traits to apply to characters of this species."""


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


class SettlementDef(ContentDefinition):
    """A definition for a settlement."""

    definition_id: str
    """The name of this definition"""
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
    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""


class ResidenceDef(ContentDefinition):
    """A definition for a residential building."""

    definition_id: str
    """The name of this definition"""
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
    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""

    @property
    def is_multifamily(self) -> bool:
        """Is this a multifamily residential building"""
        return self.residential_units > 1


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


class CharacterDef(ContentDefinition):
    """A definition for a character that can spawn into the world."""

    definition_id: str
    """The name of this definition."""
    traits: list[CharacterDefTraitEntry] = pydantic.Field(default_factory=list)
    """Default traits applied to the character during generation."""
    skills: list[CharacterDefSkillEntry] = pydantic.Field(default_factory=list)
    """Default skills applied to the character upon generation."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""
    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""


class JobRoleDef(ContentDefinition):
    """A definition of a type of job characters can work at a business."""

    definition_id: str
    """The name of this definition."""
    name: str
    """The name of the role."""
    description: str = ""
    """A description of the role."""
    job_level: int = 1
    """General level of prestige associated with this role."""
    requirements: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Precondition query statements for this role."""
    effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Effects applied when a character holds this role."""
    recurring_effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Effects reapplied each time step."""
    variants: list[dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Variant settings of this type."""
    extends: list[str] = pydantic.Field(default_factory=list)
    """Definition IDs of definitions this inherits properties from."""
    is_template: bool = False
    """Is this definition a template for creating other definitions."""
    tags: set[str] = pydantic.Field(default_factory=set)
    """Tags describing this definition."""


class BusinessDef(ContentDefinition):
    """A definition for a business where characters can work and meet people."""

    definition_id: str
    """The name of this definition."""
    traits: list[str] = pydantic.Field(default_factory=list)
    """Traits this business starts with."""
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
    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""


class BeliefDef(ContentDefinition):
    """A definition for a belief held by an agent."""

    description: str
    """A text description of the belief."""
    preconditions: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Relationship preconditions for the belief to take effect."""
    effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Effects applied to a relationship by the belief."""
    is_global: bool = False
    """Is this belief held by all agents."""


class LocationPreferenceDef(ContentDefinition):
    """A rule that helps characters score how they feel about locations to frequent."""

    preconditions: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Precondition to run when scoring a location."""
    probability: float
    """The amount to apply to the score."""
