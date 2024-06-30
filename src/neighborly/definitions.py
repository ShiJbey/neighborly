"""Neighborly Content Definitions and Definition Compiler.

This script contains a best attempt at recreating the YAML configuration file workflow
described by Patrick Kemp @ Spry Fox Games.

It is based on this talk:
https://www.youtube.com/watch?v=rWPJ5fW1UH8&t=538s

This script aims to reproduce the following capabilities:

1) Allow definitions to include other definitions as boilerplate data
2) Enable users to specify definition variants that expand to final definitions
3) Support additive tags. So a definition's tag set is a combination of its
   tags and the tags of any parent definitions.

"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Type, TypeVar

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

    spawn_frequency: int = 1
    """The relative frequency of this district spawning compared to others."""
    max_instances: int = 1
    """The maximum instances of this district that can exist in a settlement."""
    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""


class SkillDef(ContentDefinition):
    """A definition for a skill."""

    name: str = ""
    """The skill's name."""
    description: str = ""
    """A short description of the skill."""
    spawn_frequency: int = 1
    """The relative frequency of a character spawning with this skill."""


class TraitDef(ContentDefinition):
    """A definition for a trait."""

    name: str
    """The name of this trait."""
    description: str = ""
    """A short description of the trait."""
    effects: list[dict[str, Any]] = pydantic.Field(default_factory=list)
    """Effects applied when a GameObject has this trait."""
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


class SpeciesDef(ContentDefinition):
    """A definition for a species type."""

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
    adolescent_male_fertility: int
    """Max fertility for adolescent males."""
    young_adult_male_fertility: int
    """Max fertility for young adult males."""
    adult_male_fertility: int
    """Max fertility for adult males."""
    senior_male_fertility: int
    """Max fertility for senior males."""
    adolescent_female_fertility: int
    """Max fertility for adolescent females."""
    young_adult_female_fertility: int
    """Max fertility for young adult females."""
    adult_female_fertility: int
    """Max fertility for adult females."""
    senior_female_fertility: int
    """Max fertility for senior females."""
    fertility_cost_per_child: int
    """Fertility reduction each time a character births a child."""
    can_physically_age: bool = True
    """Does this character go through the various life stages."""
    traits: list[str] = pydantic.Field(default_factory=list)
    """Traits to apply to characters of this species."""


class SettlementDef(ContentDefinition):
    """A definition for a settlement."""

    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""


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

    traits: list[CharacterDefTraitEntry] = pydantic.Field(default_factory=list)
    """Default traits applied to the character during generation."""
    skills: list[CharacterDefSkillEntry] = pydantic.Field(default_factory=list)
    """Default skills applied to the character upon generation."""
    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""


class JobRoleDef(ContentDefinition):
    """A definition of a type of job characters can work at a business."""

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


class BusinessDef(ContentDefinition):
    """A definition for a business where characters can work and meet people."""

    traits: list[str] = pydantic.Field(default_factory=list)
    """Traits this business starts with."""
    spawn_frequency: int = 1
    """The frequency of spawning relative to others in the district."""
    min_population: int = 0
    """The minimum number of residents required to spawn the business."""
    max_instances: int = 9999
    """The maximum number of this definition that may exist in a district."""
    components: dict[str, dict[str, Any]] = pydantic.Field(default_factory=dict)
    """Information about components."""


_T = TypeVar("_T", bound=ContentDefinition)


def compile_definitions(
    definitions: Iterable[_T],
) -> list[_T]:
    """Compile final definitions from a collection of raw definitions."""

    unprocessed_defs: dict[str, _T] = {d.definition_id: d for d in definitions}
    processed_defs: dict[str, _T] = {}

    for definition in definitions:

        if definition.definition_id in processed_defs:
            # This one was already processed while processing another.
            continue

        _process_definition(
            type(definition), definition, unprocessed_defs, processed_defs
        )

    final_results: list[_T] = []

    for definition in processed_defs.values():
        definition.extends.clear()
        definition.variants.clear()
        final_results.append(definition)

    return final_results


def _process_definition(
    definition_type: Type[_T],
    definition: _T,
    unprocessed_defs: dict[str, _T],
    processed_defs: dict[str, _T],
) -> None:
    """Compile a single definition."""
    # We have to do the following to ensure that 'is_template' has the 'set' flag
    # and is not excluded from model_dump(...)
    if definition.is_template is False:
        definition.is_template = False

    # Variables to hold cumulative definition data
    final_definition_data: dict[str, Any] = {}
    final_definition_tags: set[str] = set()
    final_definition_components: dict[str, dict[str, Any]] = {}

    # Update the final definition data with all the parents data
    for parent_def_id in definition.extends:
        if parent_def_id not in processed_defs:
            _process_definition(
                definition_type,
                unprocessed_defs[parent_def_id],
                unprocessed_defs,
                processed_defs,
            )

        parent_def = processed_defs[parent_def_id]

        # Update cumulative variables with parent data
        parent_def_raw = parent_def.model_dump(exclude_unset=True)
        final_definition_data.update(parent_def_raw)
        final_definition_tags = final_definition_tags.union(parent_def.tags)
        if "components" in parent_def_raw:
            final_definition_components.update(parent_def_raw["components"])

    # Lastly update cumulative variables with the current definition's data
    raw_definition = definition.model_dump(exclude_unset=True)
    final_definition_data.update(raw_definition)
    if "components" in raw_definition:
        final_definition_components.update(raw_definition["components"])
    final_definition_data["components"] = final_definition_components
    final_definition_data["tags"] = final_definition_tags.union(definition.tags)

    # This definition has been processed.
    final_definition = definition_type.model_validate(final_definition_data)
    processed_defs[final_definition.definition_id] = final_definition

    # Process any variants
    for variant_def in final_definition.variants:
        # We have to do the following to ensure that 'is_template' has the
        # 'set' flag and is not excluded from model_dump(...)
        if "variant_name" not in variant_def:
            raise ValueError(
                f"{final_definition.definition_id} has variant that is missing a name."
            )

        variant_name = variant_def["variant_name"]
        variant_tags: set[str] = set(variant_def.get("tags", []))

        variant_definition_data: dict[str, Any] = {}

        variant_definition_data.update(final_definition.model_dump(exclude_unset=True))

        variant_definition_data.update(variant_def)

        variant_id = f"{final_definition.definition_id}.{variant_name}"
        variant_definition_data["definition_id"] = variant_id
        variant_definition_data["tags"] = final_definition.tags.union(variant_tags)
        variant_definition_data["components"] = {
            **final_definition_data.get("components", {}),
            **variant_definition_data.get("components", {}),
        }

        processed_defs[variant_id] = definition_type.model_validate(
            variant_definition_data
        )
