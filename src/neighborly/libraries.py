"""Content libraries.

All content that can be authored or configured using external data files is collected
in a library. This makes it easy to look up any authored content using its definition
ID.

"""

from __future__ import annotations

import json
from abc import abstractmethod
from collections import defaultdict
from typing import Any, Generic, Iterable, Optional, Protocol, Type, TypeVar

import pydantic
from ordered_set import OrderedSet

from neighborly.action import ActionConsideration
from neighborly.components.location import LocationPreferenceRule
from neighborly.components.relationship import SocialRule
from neighborly.defs.base_types import (
    BusinessDef,
    BusinessGenOptions,
    CharacterDef,
    CharacterGenOptions,
    ContentDefinition,
    DistrictDef,
    DistrictGenOptions,
    JobRoleDef,
    ResidenceDef,
    SettlementDef,
    SettlementGenOptions,
    SkillDef,
    TraitDef,
)
from neighborly.ecs import World
from neighborly.helpers.content_selection import get_with_tags

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


class ICharacterNameFactory(Protocol):
    """Generates a character name."""

    @abstractmethod
    def __call__(self, world: World, options: CharacterGenOptions) -> str:
        """Generate a new name."""
        raise NotImplementedError()


class CharacterNameFactories:
    """A Collection of factories that generate character names."""

    __slots__ = ("factories",)

    factories: dict[str, ICharacterNameFactory]
    """Factories indexed by name."""

    def __init__(self) -> None:
        self.factories = {}

    def add_factory(self, name: str, factory: ICharacterNameFactory) -> None:
        """Add a factory."""
        self.factories[name] = factory

    def get_factory(self, name: str) -> ICharacterNameFactory:
        """Get a factory by name."""
        return self.factories[name]


class IBusinessNameFactory(Protocol):
    """Generates business names."""

    @abstractmethod
    def __call__(self, world: World, options: BusinessGenOptions) -> str:
        """Generate a new name."""
        raise NotImplementedError()


class BusinessNameFactories:
    """A collection of factories that generate business names."""

    __slots__ = ("factories",)

    factories: dict[str, IBusinessNameFactory]
    """Factories indexed by name."""

    def __init__(self) -> None:
        self.factories = {}

    def add_factory(self, name: str, factory: IBusinessNameFactory) -> None:
        """Add a factory."""
        self.factories[name] = factory

    def get_factory(self, name: str) -> IBusinessNameFactory:
        """Get a factory by name."""
        return self.factories[name]


class IDistrictNameFactory(Protocol):
    """Generates district names."""

    @abstractmethod
    def __call__(self, world: World, options: DistrictGenOptions) -> str:
        """Generate a new name."""
        raise NotImplementedError()


class DistrictNameFactories:
    """A collection of factories that generate district names."""

    __slots__ = ("factories",)

    factories: dict[str, IDistrictNameFactory]
    """Factories indexed by name."""

    def __init__(self) -> None:
        self.factories = {}

    def add_factory(self, name: str, factory: IDistrictNameFactory) -> None:
        """Add a factory."""
        self.factories[name] = factory

    def get_factory(self, name: str) -> IDistrictNameFactory:
        """Get a factory by name."""
        return self.factories[name]


class ISettlementNameFactory(Protocol):
    """Generates settlement names."""

    @abstractmethod
    def __call__(self, world: World, options: SettlementGenOptions) -> str:
        """Generate a new name."""
        raise NotImplementedError()


class SettlementNameFactories:
    """A collection of factories that generate settlement names."""

    __slots__ = ("factories",)

    factories: dict[str, ISettlementNameFactory]
    """Factories indexed by name."""

    def __init__(self) -> None:
        self.factories = {}

    def add_factory(self, name: str, factory: ISettlementNameFactory) -> None:
        """Add a factory."""
        self.factories[name] = factory

    def get_factory(self, name: str) -> ISettlementNameFactory:
        """Get a factory by name."""
        return self.factories[name]


class ActionConsiderationLibrary:
    """Manages all considerations that calculate the probability of a potential action.

    All considerations are grouped by action ID. End-users are responsible for casting
    the action instance if they care about type hints and such.
    """

    __slots__ = ("success_considerations", "utility_considerations")

    success_considerations: defaultdict[str, OrderedSet[ActionConsideration]]
    """Considerations for calculating success probabilities."""

    utility_considerations: defaultdict[str, OrderedSet[ActionConsideration]]
    """Considerations for calculating utility scores."""

    def __init__(self) -> None:
        self.success_considerations = defaultdict(OrderedSet)
        self.utility_considerations = defaultdict(OrderedSet)

    def add_success_consideration(
        self, action_id: str, consideration: ActionConsideration
    ) -> None:
        """Add a success consideration to the library."""
        self.success_considerations[action_id].add(consideration)

    def add_utility_consideration(
        self, action_id: str, consideration: ActionConsideration
    ) -> None:
        """Add a utility consideration to the library."""
        self.utility_considerations[action_id].add(consideration)

    def remove_success_consideration(
        self, action_id: str, consideration: ActionConsideration
    ) -> None:
        """Remove a success consideration from the library."""
        self.success_considerations[action_id].remove(consideration)

    def remove_utility_consideration(
        self, action_id: str, consideration: ActionConsideration
    ) -> None:
        """Remove a utility consideration from the library."""
        self.utility_considerations[action_id].remove(consideration)

    def remove_all_success_considerations(self, action_id: str) -> None:
        """Add a success consideration to the library."""
        del self.success_considerations[action_id]

    def remove_all_utility_considerations(self, action_id: str) -> None:
        """Add a utility consideration to the library."""
        del self.utility_considerations[action_id]

    def get_success_considerations(
        self, action_id: str
    ) -> Iterable[ActionConsideration]:
        """Get all success considerations for an action."""
        return self.success_considerations[action_id]

    def get_utility_considerations(
        self, action_id: str
    ) -> Iterable[ActionConsideration]:
        """Get all utility considerations for an action."""
        return self.utility_considerations[action_id]
