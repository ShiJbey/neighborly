"""Content libraries.

All content that can be authored or configured using external data files is collected
in a library. This makes it easy to look up any authored content using its definition
ID.

"""

from __future__ import annotations

import json
from typing import Any, Generic, Iterable, Optional, Type, TypeVar

import pydantic

from neighborly.components.location import LocationPreferenceRule
from neighborly.components.relationship import SocialRule
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
from neighborly.helpers.content_selection import get_with_tags
from neighborly.life_event import LifeEvent

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


class TraitLibrary(ContentDefinitionLibrary[TraitDef]):
    """Manages trait definitions and instances."""


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


class BusinessLibrary(ContentDefinitionLibrary[BusinessDef]):
    """A collection of all business definitions."""


class LifeEventLibrary:
    """Manages the collection of LifeEvents that characters choose from for behavior."""

    __slots__ = ("event_types",)

    event_types: dict[str, dict[str, Type[LifeEvent]]]
    """Life event types organized by agent type and event id."""

    def __init__(self) -> None:
        self.event_types = {}

    def add_event_type(self, agent_type: str, event_type: Type[LifeEvent]) -> None:
        """Add an action to the library."""
        event_id = event_type.__event_id__

        if event_id not in self.event_types:
            self.event_types[agent_type] = {}

        self.event_types[agent_type][event_id] = event_type

    def get_event_type(self, agent_type: str, event_id: str) -> Type[LifeEvent]:
        """Get an action from teh library."""
        if agent_type not in self.event_types:
            raise KeyError(f"Could not find action entries for {agent_type!r}")

        action_subset = self.event_types[agent_type]

        if event_id not in action_subset:
            raise KeyError(f"Could not find {event_id!r} event for {agent_type!r}")

        return action_subset[event_id]

    def get_all_event_types(self, agent_type: str) -> Iterable[Type[LifeEvent]]:
        """Get an action from teh library."""
        if agent_type not in self.event_types:
            return []

        return self.event_types[agent_type].values()


class SocialRuleLibrary:
    """The collection of social rules for relationships."""

    __slots__ = ("rules",)

    rules: dict[str, SocialRule]
    """Rules applied to the owning GameObject's relationships."""

    def __init__(self) -> None:
        super().__init__()
        self.rules = {}

    def add_rule(self, rule: SocialRule) -> None:
        """Add a rule to the rule collection."""
        self.rules[rule.rule_id] = rule


class LocationPreferenceLibrary:
    """The collection of location preference rules."""

    __slots__ = ("rules",)

    rules: dict[str, LocationPreferenceRule]
    """Rules added to the location preferences."""

    def __init__(self) -> None:
        super().__init__()
        self.rules = {}

    def add_rule(self, rule: LocationPreferenceRule) -> None:
        """Add a location preference rule."""
        self.rules[rule.rule_id] = rule
