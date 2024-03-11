"""Content libraries.

All content that can be authored or configured using external data files is collected
in a library. This makes it easy to look up any authored content using its definition
ID.

"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Iterator, Type

from ordered_set import OrderedSet

from neighborly.components.business import JobRole
from neighborly.components.location import LocationPreferenceRule
from neighborly.components.relationship import SocialRule
from neighborly.components.skills import Skill
from neighborly.components.traits import Trait
from neighborly.defs.base_types import (
    BusinessDef,
    CharacterDef,
    DistrictDef,
    JobRoleDef,
    ResidenceDef,
    SettlementDef,
    SkillDef,
    SpeciesDef,
    TraitDef,
)
from neighborly.ecs import GameObject
from neighborly.effects.base_types import Effect
from neighborly.helpers.content_selection import get_with_tags
from neighborly.life_event import LifeEvent, LifeEventConsideration


class SkillLibrary:
    """The collection of skill definitions and instances."""

    _slots__ = (
        "definitions",
        "instances",
    )

    instances: dict[str, GameObject]
    """Skill IDs mapped to instances of the skill."""
    definitions: dict[str, SkillDef]
    """Skill IDs mapped to skill definition instances."""

    def __init__(self) -> None:
        self.instances = {}
        self.definitions = {}

    def get_skill(self, skill_id: str) -> GameObject:
        """Get a skill instance given an ID."""

        return self.instances[skill_id]

    def add_skill(self, skill: GameObject) -> None:
        """Add a skill instance to the library."""

        self.instances[skill.get_component(Skill).definition_id] = skill

    def get_definition(self, definition_id: str) -> SkillDef:
        """Get a definition from the library."""

        return self.definitions[definition_id]

    def add_definition(self, skill_def: SkillDef) -> None:
        """Add a definition to the library."""

        self.definitions[skill_def.definition_id] = skill_def

    def get_definition_with_tags(self, tags: list[str]) -> list[SkillDef]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )


class TraitLibrary:
    """The collection of trait definitions and instances."""

    _slots__ = (
        "definitions",
        "instances",
    )

    instances: dict[str, GameObject]
    """Trait IDs mapped to instances of definitions."""
    definitions: dict[str, TraitDef]
    """Definition instances added to the library."""

    def __init__(self) -> None:
        self.instances = {}
        self.definitions = {}

    def get_trait(self, trait_id: str) -> GameObject:
        """Get a trait instance given an ID."""

        return self.instances[trait_id]

    def add_trait(self, trait: GameObject) -> None:
        """Add a trait instance to the library."""

        self.instances[trait.get_component(Trait).definition_id] = trait

    def get_definition(self, definition_id: str) -> TraitDef:
        """Get a definition instance from the library."""

        return self.definitions[definition_id]

    def add_definition(self, trait_def: TraitDef) -> None:
        """Add a definition instance to the library."""

        self.definitions[trait_def.definition_id] = trait_def

    def get_definition_with_tags(self, tags: list[str]) -> list[TraitDef]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )


class SpeciesLibrary:
    """The collection of species definitions and instances."""

    _slots__ = (
        "definitions",
        "instances",
    )

    instances: dict[str, GameObject]
    """Species IDs mapped to GameObject instances."""
    definitions: dict[str, SpeciesDef]
    """Species IDs mapped to definitions."""

    def __init__(self) -> None:
        self.instances = {}
        self.definitions = {}

    def get_species(self, species_id: str) -> GameObject:
        """Get a species instance given an ID."""

        return self.instances[species_id]

    def add_species(self, species: GameObject) -> None:
        """Add a species instance to the library."""

        self.instances[species.get_component(Trait).definition_id] = species

    def get_definition(self, definition_id: str) -> SpeciesDef:
        """Get a definition from the library."""

        return self.definitions[definition_id]

    def add_definition(self, species_def: SpeciesDef) -> None:
        """Add a definition to the library."""

        self.definitions[species_def.definition_id] = species_def


class EffectLibrary:
    """Manages effect types for easy lookup at runtime."""

    __slots__ = ("effect_types",)

    effect_types: dict[str, Type[Effect]]
    """SettlementDef types for loading data from config files."""

    def __init__(self) -> None:
        self.effect_types = {}

    def get_event(self, name: str) -> Type[Effect]:
        """Get a factory"""
        return self.effect_types[name]

    def add_event(self, factory: Type[Effect]) -> None:
        """Add a factory."""
        self.effect_types[factory.__name__] = factory


class DistrictLibrary:
    """A collection of all district definitions."""

    __slots__ = ("definitions",)

    definitions: dict[str, DistrictDef]
    """Definition instances added to the library."""

    def __init__(self) -> None:
        self.definitions = {}

    def get_definition(self, definition_id: str) -> DistrictDef:
        """Get a definition from the library."""

        return self.definitions[definition_id]

    def add_definition(self, district_def: DistrictDef) -> None:
        """Add a definition to the library."""

        self.definitions[district_def.definition_id] = district_def

    def get_definition_with_tags(self, tags: list[str]) -> list[DistrictDef]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )


class SettlementLibrary:
    """The Collection of all the settlement definitions."""

    __slots__ = ("definitions",)

    definitions: dict[str, SettlementDef]

    def __init__(self) -> None:
        self.definitions = {}

    def get_definition(self, definition_id: str) -> SettlementDef:
        """Get a definition from the library."""

        return self.definitions[definition_id]

    def add_definition(self, settlement_def: SettlementDef) -> None:
        """Add a definition to the library."""

        self.definitions[settlement_def.definition_id] = settlement_def

    def get_definition_with_tags(self, tags: list[str]) -> list[SettlementDef]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )


class ResidenceLibrary:
    """A collection of all character definitions."""

    __slots__ = ("definitions",)

    definitions: dict[str, ResidenceDef]
    """Definition instances added to the library."""

    def __init__(self) -> None:
        self.definitions = {}

    def get_definition(self, definition_id: str) -> ResidenceDef:
        """Get a definition instance from the library."""

        return self.definitions[definition_id]

    def add_definition(self, residence_def: ResidenceDef) -> None:
        """Add a definition instance to the library."""

        self.definitions[residence_def.definition_id] = residence_def

    def get_definition_with_tags(self, tags: list[str]) -> list[ResidenceDef]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )


class CharacterLibrary:
    """A collection of all character definitions."""

    __slots__ = ("definitions",)

    definitions: dict[str, CharacterDef]
    """Definition instances added to the library."""

    def __init__(self) -> None:
        self.definitions = {}

    def get_definition(self, definition_id: str) -> CharacterDef:
        """Get a definition instance from the library."""

        return self.definitions[definition_id]

    def add_definition(self, character_def: CharacterDef) -> None:
        """Add a definition instance to the library."""

        self.definitions[character_def.definition_id] = character_def

    def get_definition_with_tags(self, tags: list[str]) -> list[CharacterDef]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )


class JobRoleLibrary:
    """Manages trait definitions and trait instances."""

    _slots__ = (
        "definitions",
        "job_role_instances",
    )

    job_role_instances: dict[str, GameObject]
    """IDs mapped to instances of job roles."""
    definitions: dict[str, JobRoleDef]
    """Definition instances added to the library."""

    def __init__(self) -> None:
        self.job_role_instances = {}
        self.definitions = {}

    @property
    def job_role_ids(self) -> Iterable[str]:
        """The definition IDs of instantiated job roles."""
        return self.definitions.keys()

    def get_role(self, job_role_id: str) -> GameObject:
        """Get a job role instance given an ID."""
        return self.job_role_instances[job_role_id]

    def add_role(self, job_role: GameObject) -> None:
        """Add a job role instance to the library."""
        self.job_role_instances[job_role.get_component(JobRole).definition_id] = (
            job_role
        )

    def get_definition(self, definition_id: str) -> JobRoleDef:
        """Get a definition instance from the library."""
        return self.definitions[definition_id]

    def add_definition(self, job_role_def: JobRoleDef) -> None:
        """Add a definition instance to the library."""
        self.definitions[job_role_def.definition_id] = job_role_def


class BusinessLibrary:
    """A collection of all business definitions."""

    __slots__ = ("definitions",)

    definitions: dict[str, BusinessDef]
    """Definition instances added to the library."""

    def __init__(self) -> None:
        self.definitions = {}

    def get_definition(self, definition_id: str) -> BusinessDef:
        """Get a definition instance from the library."""
        return self.definitions[definition_id]

    def add_definition(self, business_def: BusinessDef) -> None:
        """Add a definition instance to the library."""
        self.definitions[business_def.definition_id] = business_def

    def get_definition_with_tags(self, tags: list[str]) -> list[BusinessDef]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )


class LifeEventLibrary:
    """The collection of all life events."""

    __slots__ = ("_event_types",)

    _event_types: OrderedSet[Type[LifeEvent]]
    """Collection of all LifeEvent subtypes that have been added to the library."""

    def __init__(self) -> None:
        self._event_types = OrderedSet([])

    def add_event_type(self, event_type: Type[LifeEvent]) -> None:
        """Add a LifeEvent subtype to the library."""
        self._event_types.add(event_type)

    def __iter__(self) -> Iterator[Type[LifeEvent]]:
        return iter(self._event_types)


class SocialRuleLibrary:
    """The collection of social rules for relationships."""

    __slots__ = ("rules",)

    rules: list[SocialRule]
    """Rules applied to the owning GameObject's relationships."""

    def __init__(self) -> None:
        super().__init__()
        self.rules = []

    def add_rule(self, rule: SocialRule) -> None:
        """Add a rule to the rule collection."""
        self.rules.append(rule)


class LocationPreferenceRuleLibrary:
    """The collection of location preference rules."""

    __slots__ = ("rules",)

    rules: list[LocationPreferenceRule]
    """Rules added to the location preferences."""

    def __init__(self) -> None:
        super().__init__()
        self.rules = []

    def add_rule(self, rule: LocationPreferenceRule) -> None:
        """Add a location preference rule."""
        self.rules.append(rule)


class LifeEventConsiderationLibrary:
    """The shared collection of life event considerations."""

    __slots__ = ("considerations",)

    considerations: defaultdict[str, list[LifeEventConsideration]]
    """Consideration for life events."""

    def __init__(self) -> None:
        self.considerations = defaultdict(list)

    def add_consideration(
        self,
        event_name: str,
        consideration: LifeEventConsideration,
    ) -> None:
        """Add a consideration to the collection.

        Parameters
        ----------
        event_name
            The event type the consideration is for.
        consideration
            The consideration.
        """

        self.considerations[event_name].append(consideration)

    def get_event_considerations(
        self, event_name: str
    ) -> Iterable[LifeEventConsideration]:
        """Get all considerations for a given type.

        Parameters
        ----------
        event_name
            The event type to get considerations for.

        Returns
        -------
        Iterable[LifeEventConsideration]
            All the added considerations for this event type
        """

        return self.considerations[event_name]
