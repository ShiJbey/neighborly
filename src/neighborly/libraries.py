"""Content libraries.

All content that can be authored or configured using external data files is collected
in a library. This makes it easy to look up any authored content using its definition
ID.

"""

from __future__ import annotations

import json
from typing import Any, Generic, Iterable, Iterator, Optional, Type, TypeVar

import pydantic
from ordered_set import OrderedSet

from neighborly.components.business import JobRole
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
from neighborly.ecs import GameObject, World
from neighborly.effects.base_types import Effect
from neighborly.helpers.content_selection import get_with_tags
from neighborly.life_event import LifeEvent
from neighborly.preconditions.base_types import Precondition

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
        definition_key = alias if alias else definition_type.__name__

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
    """Manages skill definitions and instances."""

    _slots__ = ("instances",)

    instances: dict[str, GameObject]
    """Definition IDs mapped to skill GameObjects."""

    def __init__(
        self, default_definition_type: Optional[Type[SkillDef]] = None
    ) -> None:
        super().__init__(default_definition_type)
        self.instances = {}

    @property
    def skill_ids(self) -> Iterable[str]:
        """The definition IDs of instantiated skills."""
        return self.instances.keys()

    def get_skill(self, skill_id: str) -> GameObject:
        """Get a skill instance given an ID."""
        return self.instances[skill_id]

    def add_skill(self, skill: GameObject) -> None:
        """Add a skill instance to the library."""
        self.instances[skill.get_component(Skill).definition_id] = skill


class TraitLibrary(ContentDefinitionLibrary[TraitDef]):
    """Manages trait definitions and instances."""

    _slots__ = ("instances",)

    instances: dict[str, GameObject]
    """Definition IDs mapped to trait GameObjects."""

    def __init__(
        self, default_definition_type: Optional[Type[TraitDef]] = None
    ) -> None:
        super().__init__(default_definition_type)
        self.instances = {}

    @property
    def trait_ids(self) -> Iterable[str]:
        """The definition IDs of instantiated traits."""
        return self.instances.keys()

    def get_trait(self, trait_id: str) -> GameObject:
        """Get a trait instance given an ID."""
        return self.instances[trait_id]

    def add_trait(self, trait: GameObject) -> None:
        """Add a trait instance to the library."""
        self.instances[trait.get_component(Trait).definition_id] = trait


class PreconditionLibrary:
    """Manages effect precondition types and constructs them when needed."""

    _slots__ = "_precondition_types"

    _precondition_types: dict[str, Type[Precondition]]
    """Precondition types for loading data from config files."""

    def __init__(self) -> None:
        self._precondition_types = {}

    def get_precondition_type(self, precondition_name: str) -> Type[Precondition]:
        """Get a definition type."""
        return self._precondition_types[precondition_name]

    def add_precondition_type(self, precondition_type: Type[Precondition]) -> None:
        """Add a definition type for loading objs."""
        self._precondition_types[precondition_type.__name__] = precondition_type

    def create_from_obj(self, world: World, obj: dict[str, Any]) -> Precondition:
        """Parse a definition from a dict and add to the library."""
        params = {**obj}
        precondition_name: str = params["type"]
        del params["type"]

        precondition_type = self.get_precondition_type(precondition_name)
        precondition = precondition_type.instantiate(world, params)

        return precondition


class EffectLibrary:
    """Manages effect types and constructs them when needed."""

    _slots__ = "_effect_types"

    _effect_types: dict[str, Type[Effect]]
    """SettlementDef types for loading data from config files."""

    def __init__(self) -> None:
        self._effect_types = {}

    def get_effect_type(self, effect_name: str) -> Type[Effect]:
        """Get a definition type."""
        return self._effect_types[effect_name]

    def add_effect_type(self, effect_type: Type[Effect]) -> None:
        """Add a definition type for loading objs."""
        self._effect_types[effect_type.__name__] = effect_type

    def create_from_obj(self, world: World, obj: dict[str, Any]) -> Effect:
        """Parse a definition from a dict and add to the library."""
        params = {**obj}
        effect_name: str = params["type"]
        del params["type"]

        effect_type = self.get_effect_type(effect_name)
        effect = effect_type.instantiate(world, params)

        return effect


class DistrictLibrary(ContentDefinitionLibrary[DistrictDef]):
    """A collection of all district definitions."""


class SettlementLibrary(ContentDefinitionLibrary[SettlementDef]):
    """A Collection of all the settlement definitions."""


class ResidenceLibrary(ContentDefinitionLibrary[ResidenceDef]):
    """A collection of all character definitions."""


class CharacterLibrary(ContentDefinitionLibrary[CharacterDef]):
    """A collection of all character definitions."""


class JobRoleLibrary(ContentDefinitionLibrary[JobRoleDef]):
    """Manages job role definitions and instances."""

    _slots__ = "instances"

    instances: dict[str, GameObject]
    """Definition IDs mapped to job role GameObjects."""

    def __init__(
        self, default_definition_type: Optional[Type[JobRoleDef]] = None
    ) -> None:
        super().__init__(default_definition_type)
        self.instances = {}

    @property
    def job_role_ids(self) -> Iterable[str]:
        """The definition IDs of instantiated job roles."""
        return self.definitions.keys()

    def get_role(self, job_role_id: str) -> GameObject:
        """Get a job role instance given an ID."""
        return self.instances[job_role_id]

    def add_role(self, job_role: GameObject) -> None:
        """Add a job role instance to the library."""
        self.instances[job_role.get_component(JobRole).definition_id] = job_role


class BusinessLibrary(ContentDefinitionLibrary[BusinessDef]):
    """A collection of all business definitions."""


class LifeEventLibrary:
    """Manages the collection of LifeEvents that characters choose from for behavior."""

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
