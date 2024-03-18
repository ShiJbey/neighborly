"""Content libraries.

All content that can be authored or configured using external data files is collected
in a library. This makes it easy to look up any authored content using its definition
ID.

"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Generic, Iterable, Iterator, Optional, Type, TypeVar

import pydantic
from ordered_set import OrderedSet

from neighborly.components.business import JobRole
from neighborly.components.location import LocationPreferenceRule
from neighborly.components.relationship import SocialRule
from neighborly.components.skills import Skill
from neighborly.components.traits import Trait
from neighborly.defs.base_types import (
    BusinessDef,
    CharacterDef,
    ContentDefinition,
    DistrictDef,
    JobRoleDef,
    ResidenceDef,
    SettlementDef,
    SkillDef,
    TraitDef,
)
from neighborly.ecs import GameObject
from neighborly.effects.base_types import Effect
from neighborly.helpers.content_selection import get_with_tags
from neighborly.life_event import LifeEvent, LifeEventConsideration

_T = TypeVar("_T", bound=ContentDefinition)


class ContentDefinitionLibrary(Generic[_T]):
    """The collection of skill definitions and instances."""

    _slots__ = (
        "definitions",
        "definition_types",
        "default_definition_type",
    )

    definitions: dict[str, _T]
    """IDs mapped to definition instances."""
    definition_types: dict[str, Type[_T]]
    """IDs mapped to definition class types."""
    default_definition_type: str
    """The type name of the definition to use when importing raw data."""

    def __init__(self, default_definition_type: Optional[Type[_T]] = None) -> None:
        self.definitions = {}
        self.definition_types = {}
        self.default_definition_type = ""

        if default_definition_type:
            self.add_definition_type(default_definition_type, set_default=True)

    def get_definition(self, definition_id: str) -> _T:
        """Get a definition from the library."""

        return self.definitions[definition_id]

    def add_definition(self, definition: _T) -> None:
        """Add a definition to the library."""

        self.definitions[definition.definition_id] = definition

    def get_definition_with_tags(self, tags: list[str]) -> list[_T]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )

    def add_definition_type(
        self,
        definition_type: Type[_T],
        set_default: bool = False,
        alias: str = "",
    ) -> None:
        """Add a definition type to the library."""
        definition_key = alias if alias else definition_type.__class__.__name__

        self.definition_types[definition_key] = definition_type

        if set_default:
            self.default_definition_type = definition_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""

        definition_type_name: str = obj.get(
            "definition_type", self.default_definition_type
        )
        definition_type = self.definition_types[definition_type_name]

        try:
            definition = definition_type.model_validate(obj)
            self.add_definition(definition)

        except pydantic.ValidationError as err:
            raise RuntimeError(
                f"Error while parsing definition: {err!r}.\n"
                f"{json.dumps(obj, indent=2)}"
            ) from err

        except TypeError as err:
            raise RuntimeError(
                f"Error while parsing definition: {err!r}.\n"
                f"{json.dumps(obj, indent=2)}"
            ) from err


class SkillLibrary(ContentDefinitionLibrary[SkillDef]):
    """The collection of skill definitions and instances."""

    _slots__ = "instances"

    instances: dict[str, GameObject]
    """Skill IDs mapped to instances of the skill."""

    def __init__(
        self, default_definition_type: Optional[Type[SkillDef]] = None
    ) -> None:
        super().__init__(default_definition_type)
        self.instances = {}

    def get_skill(self, skill_id: str) -> GameObject:
        """Get a skill instance given an ID."""

        return self.instances[skill_id]

    def add_skill(self, skill: GameObject) -> None:
        """Add a skill instance to the library."""

        self.instances[skill.get_component(Skill).definition_id] = skill


class TraitLibrary(ContentDefinitionLibrary[TraitDef]):
    """The collection of trait definitions and instances."""

    _slots__ = ("instances",)

    instances: dict[str, GameObject]
    """Trait IDs mapped to instances of definitions."""

    def __init__(
        self, default_definition_type: Optional[Type[TraitDef]] = None
    ) -> None:
        super().__init__(default_definition_type)
        self.instances = {}

    def get_trait(self, trait_id: str) -> GameObject:
        """Get a trait instance given an ID."""

        return self.instances[trait_id]

    def add_trait(self, trait: GameObject) -> None:
        """Add a trait instance to the library."""

        self.instances[trait.get_component(Trait).definition_id] = trait


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


class DistrictLibrary(ContentDefinitionLibrary[DistrictDef]):
    """A collection of all district definitions."""


class SettlementLibrary(ContentDefinitionLibrary[SettlementDef]):
    """The Collection of all the settlement definitions."""


class ResidenceLibrary(ContentDefinitionLibrary[ResidenceDef]):
    """A collection of all character definitions."""


class CharacterLibrary(ContentDefinitionLibrary[CharacterDef]):
    """A collection of all character definitions."""


class JobRoleLibrary(ContentDefinitionLibrary[JobRoleDef]):
    """The collection of job role definitions and instances."""

    _slots__ = ("instances",)

    instances: dict[str, GameObject]
    """IDs mapped to instances of job roles."""

    def __init__(
        self, default_definition_type: Optional[Type[JobRoleDef]] = None
    ) -> None:
        super().__init__(default_definition_type)
        self.definitions = {}

    def get_role(self, job_role_id: str) -> GameObject:
        """Get a job role instance given an ID."""
        return self.instances[job_role_id]

    def add_role(self, job_role: GameObject) -> None:
        """Add a job role instance to the library."""
        self.instances[job_role.get_component(JobRole).definition_id] = job_role


class BusinessLibrary(ContentDefinitionLibrary[BusinessDef]):
    """A collection of all business definitions."""


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
