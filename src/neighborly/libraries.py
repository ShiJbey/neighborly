"""Content libraries.

All content that can be authored or configured using external data files is collected
in a library. This makes it easy to look up any authored content using its definition
ID.

"""

from __future__ import annotations

from typing import Any, Iterable, Iterator, Type

from ordered_set import OrderedSet

from neighborly.components.business import JobRole
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
    TraitDef,
)
from neighborly.ecs import GameObject, World
from neighborly.effects.base_types import Effect
from neighborly.life_event import LifeEvent
from neighborly.preconditions.base_types import Precondition


class SkillLibrary:
    """Manages skill definitions and Skill instances."""

    _slots__ = (
        "_definitions",
        "_definition_types",
        "_skill_instances",
        "_default_definition_type",
    )

    _skill_instances: dict[str, GameObject]
    """Skill IDs mapped to instances of the skill."""
    _definitions: dict[str, SkillDef]
    """Skill IDs mapped to skill definition instances."""
    _definition_types: dict[str, Type[SkillDef]]
    """String names mapped to skill definition types."""
    _default_definition_type: str
    """The name of the default definition type used when loading data from a file."""

    def __init__(self, default_definition_type: Type[SkillDef]) -> None:
        self._skill_instances = {}
        self._definitions = {}
        self._definition_types = {}
        self._default_definition_type = ""
        self.add_definition_type(default_definition_type, set_default=True)

    @property
    def skill_ids(self) -> Iterable[str]:
        """The definition IDs of instantiated skills."""
        return self._definitions.keys()

    def get_skill(self, skill_id: str) -> GameObject:
        """Get a skill instance given an ID."""
        return self._skill_instances[skill_id]

    def add_skill(self, skill: GameObject) -> None:
        """Add a tag instance to the library."""
        self._skill_instances[skill.get_component(Skill).definition_id] = skill

    def get_definition(self, definition_id: str) -> SkillDef:
        """Get a definition instance from the library."""
        return self._definitions[definition_id]

    def add_definition(self, skill_def: SkillDef) -> None:
        """Add a definition instance to the library."""
        self._definitions[skill_def.definition_id] = skill_def

    def get_definition_type(self, definition_type_name: str) -> Type[SkillDef]:
        """Get a definition type."""
        return self._definition_types[definition_type_name]

    def add_definition_type(
        self,
        definition_type: Type[SkillDef],
        set_default: bool = False,
        alias: str = "",
    ) -> None:
        """Add a definition type for loading objs."""
        entry_key = alias if alias else definition_type.__name__
        self._definition_types[entry_key] = definition_type
        if set_default:
            self._default_definition_type = entry_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""
        definition_type_name: str = obj.get(
            "definition_type", self._default_definition_type
        )
        definition_type = self.get_definition_type(definition_type_name)
        definition = definition_type.from_obj(obj)
        self.add_definition(definition)


class TraitLibrary:
    """Manages trait definitions and trait instances."""

    _slots__ = (
        "_definitions",
        "_definition_types",
        "_trait_instances",
        "_default_definition_type",
    )

    _trait_instances: dict[str, GameObject]
    """Trait IDs mapped to instances of definitions."""
    _definitions: dict[str, TraitDef]
    """Definition instances added to the library."""
    _definition_types: dict[str, Type[TraitDef]]
    """Definition types used for loading data from files."""
    _default_definition_type: str
    """The default trait definition type to use when loading from data dict."""

    def __init__(self, default_definition_type: Type[TraitDef]) -> None:
        self._trait_instances = {}
        self._definitions = {}
        self._definition_types = {}
        self._default_definition_type = ""
        self.add_definition_type(default_definition_type, set_default=True)

    @property
    def trait_ids(self) -> Iterable[str]:
        """The definition IDs of instantiated traits."""
        return self._definitions.keys()

    def get_trait(self, trait_id: str) -> GameObject:
        """Get a trait instance given an ID."""
        return self._trait_instances[trait_id]

    def add_trait(self, trait: GameObject) -> None:
        """Add a trait instance to the library."""
        self._trait_instances[trait.get_component(Trait).definition_id] = trait

    def get_definition(self, definition_id: str) -> TraitDef:
        """Get a definition instance from the library."""
        return self._definitions[definition_id]

    def add_definition(self, trait_def: TraitDef) -> None:
        """Add a definition instance to the library."""
        self._definitions[trait_def.definition_id] = trait_def

    def get_definition_type(self, definition_type_name: str) -> Type[TraitDef]:
        """Get a definition type."""
        return self._definition_types[definition_type_name]

    def add_definition_type(
        self,
        definition_type: Type[TraitDef],
        set_default: bool = False,
        alias: str = "",
    ) -> None:
        """Add a definition type for loading objs."""
        entry_key = alias if alias else definition_type.__name__
        self._definition_types[entry_key] = definition_type
        if set_default:
            self._default_definition_type = entry_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""
        definition_type_name: str = obj.get(
            "definition_type", self._default_definition_type
        )
        definition_type = self.get_definition_type(definition_type_name)
        definition = definition_type.from_obj(obj)
        self.add_definition(definition)


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


class DistrictLibrary:
    """A collection of all district definitions."""

    __slots__ = "_definitions", "_definition_types", "_default_definition_type"

    _definitions: dict[str, DistrictDef]
    """Definition instances added to the library."""
    _definition_types: dict[str, Type[DistrictDef]]
    """SettlementDef types for loading data from config files."""
    _default_definition_type: str
    """The default definition type to use when loading from data dict."""

    def __init__(self, default_definition_type: Type[DistrictDef]) -> None:
        self._definitions = {}
        self._definition_types = {}
        self._default_definition_type = ""
        self.add_definition_type(default_definition_type, set_default=True)

    def get_definition(self, definition_id: str) -> DistrictDef:
        """Get a definition instance from the library."""
        return self._definitions[definition_id]

    def add_definition(self, district_def: DistrictDef) -> None:
        """Add a definition instance to the library."""
        self._definitions[district_def.definition_id] = district_def

    def get_definition_type(self, definition_type_name: str) -> Type[DistrictDef]:
        """Get a definition type."""
        return self._definition_types[definition_type_name]

    def add_definition_type(
        self,
        definition_type: Type[DistrictDef],
        set_default: bool = False,
        alias: str = "",
    ) -> None:
        """Add a definition type for loading objs."""
        entry_key = alias if alias else definition_type.__name__
        self._definition_types[entry_key] = definition_type
        if set_default:
            self._default_definition_type = entry_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""
        definition_type_name: str = obj.get(
            "definition_type", self._default_definition_type
        )
        definition_type = self.get_definition_type(definition_type_name)
        definition = definition_type.from_obj(obj)
        self.add_definition(definition)


class SettlementLibrary:
    """A Collection of all the settlement definitions."""

    __slots__ = "_definitions", "_definition_types", "_default_definition_type"

    _definitions: dict[str, SettlementDef]
    """Definition instances added to the library."""
    _definition_types: dict[str, Type[SettlementDef]]
    """SettlementDef types for loading data from config files."""
    _default_definition_type: str
    """The default definition type used when loading from a data dict."""

    def __init__(self, default_definition_type: Type[SettlementDef]) -> None:
        self._definitions = {}
        self._definition_types = {}
        self._default_definition_type = ""
        self.add_definition_type(default_definition_type, set_default=True)

    def get_definition(self, definition_id: str) -> SettlementDef:
        """Get a definition instance from the library."""
        return self._definitions[definition_id]

    def add_definition(self, settlement_def: SettlementDef) -> None:
        """Add a definition instance to the library."""
        self._definitions[settlement_def.definition_id] = settlement_def

    def get_definition_type(self, definition_type_name: str) -> Type[SettlementDef]:
        """Get a definition type."""
        return self._definition_types[definition_type_name]

    def add_definition_type(
        self,
        definition_type: Type[SettlementDef],
        set_default: bool = True,
        alias: str = "",
    ) -> None:
        """Add a definition type for loading objs."""
        entry_key = alias if alias else definition_type.__name__
        self._definition_types[entry_key] = definition_type
        if set_default:
            self._default_definition_type = entry_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""
        definition_type_name: str = obj.get(
            "definition_type", self._default_definition_type
        )
        definition_type = self.get_definition_type(definition_type_name)
        definition = definition_type.from_obj(obj)
        self.add_definition(definition)


class ResidenceLibrary:
    """A collection of all character definitions."""

    __slots__ = "_definitions", "_definition_types", "_default_definition_type"

    _definitions: dict[str, ResidenceDef]
    """Definition instances added to the library."""
    _definition_types: dict[str, Type[ResidenceDef]]
    """SettlementDef types for loading data from config files."""
    _default_definition_type: str
    """The default definition type to use when loading from a data dict."""

    def __init__(self, default_definition_type: Type[ResidenceDef]) -> None:
        self._definitions = {}
        self._definition_types = {}
        self._default_definition_type = ""
        self.add_definition_type(default_definition_type, set_default=True)

    def get_definition(self, definition_id: str) -> ResidenceDef:
        """Get a definition instance from the library."""
        return self._definitions[definition_id]

    def add_definition(self, residence_def: ResidenceDef) -> None:
        """Add a definition instance to the library."""
        self._definitions[residence_def.definition_id] = residence_def

    def get_definition_type(self, definition_type_name: str) -> Type[ResidenceDef]:
        """Get a definition type."""
        return self._definition_types[definition_type_name]

    def add_definition_type(
        self,
        definition_type: Type[ResidenceDef],
        set_default: bool = False,
        alias: str = "",
    ) -> None:
        """Add a definition type for loading objs."""
        entry_key = alias if alias else definition_type.__name__
        self._definition_types[entry_key] = definition_type
        if set_default:
            self._default_definition_type = entry_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""
        definition_type_name: str = obj.get(
            "definition_type", self._default_definition_type
        )
        definition_type = self.get_definition_type(definition_type_name)
        definition = definition_type.from_obj(obj)
        self.add_definition(definition)


class CharacterLibrary:
    """A collection of all character definitions."""

    __slots__ = "_definitions", "_definition_types", "_default_definition_type"

    _definitions: dict[str, CharacterDef]
    """Definition instances added to the library."""
    _definition_types: dict[str, Type[CharacterDef]]
    """SettlementDef types for loading data from config files."""
    _default_definition_type: str
    """The name of the definition type to use when one is not specified."""

    def __init__(self, default_definition_type: Type[CharacterDef]) -> None:
        self._definitions = {}
        self._definition_types = {}
        self._default_definition_type = ""
        self.add_definition_type(default_definition_type, set_default=True)

    def get_definition(self, definition_id: str) -> CharacterDef:
        """Get a definition instance from the library."""
        return self._definitions[definition_id]

    def add_definition(self, character_def: CharacterDef) -> None:
        """Add a definition instance to the library."""
        self._definitions[character_def.definition_id] = character_def

    def get_definition_type(self, definition_type_name: str) -> Type[CharacterDef]:
        """Get a definition type."""
        return self._definition_types[definition_type_name]

    def add_definition_type(
        self,
        definition_type: Type[CharacterDef],
        set_default: bool = False,
        alias: str = "",
    ) -> None:
        """Add a definition type for loading objs."""
        entry_key = alias if alias else definition_type.__name__
        self._definition_types[entry_key] = definition_type
        if set_default:
            self._default_definition_type = entry_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""
        definition_type_name: str = obj.get(
            "definition_type", self._default_definition_type
        )
        definition_type = self.get_definition_type(definition_type_name)
        definition = definition_type.from_obj(obj)
        self.add_definition(definition)


class JobRoleLibrary:
    """Manages trait definitions and trait instances."""

    _slots__ = (
        "_definitions",
        "_definition_types",
        "_job_role_instances",
        "_default_definition_type",
    )

    _job_role_instances: dict[str, GameObject]
    """IDs mapped to instances of job roles."""
    _definitions: dict[str, JobRoleDef]
    """Definition instances added to the library."""
    _definition_types: dict[str, Type[JobRoleDef]]
    """Definition types for loading data from config files."""
    _default_definition_type: str
    """The default definition type to use when loading from data dict."""

    def __init__(self, default_definition_type: Type[JobRoleDef]) -> None:
        self._job_role_instances = {}
        self._definitions = {}
        self._definition_types = {}
        self._default_definition_type = ""
        self.add_definition_type(default_definition_type, set_default=True)

    @property
    def job_role_ids(self) -> Iterable[str]:
        """The definition IDs of instantiated job roles."""
        return self._definitions.keys()

    def get_role(self, job_role_id: str) -> GameObject:
        """Get a job role instance given an ID."""
        return self._job_role_instances[job_role_id]

    def add_role(self, job_role: GameObject) -> None:
        """Add a job role instance to the library."""
        self._job_role_instances[
            job_role.get_component(JobRole).definition_id
        ] = job_role

    def get_definition(self, definition_id: str) -> JobRoleDef:
        """Get a definition instance from the library."""
        return self._definitions[definition_id]

    def add_definition(self, job_role_def: JobRoleDef) -> None:
        """Add a definition instance to the library."""
        self._definitions[job_role_def.definition_id] = job_role_def

    def get_definition_type(self, definition_type_name: str) -> Type[JobRoleDef]:
        """Get a definition type."""
        return self._definition_types[definition_type_name]

    def add_definition_type(
        self,
        definition_type: Type[JobRoleDef],
        set_default: bool = False,
        alias: str = "",
    ) -> None:
        """Add a definition type for loading objs."""
        entry_key = alias if alias else definition_type.__name__
        self._definition_types[entry_key] = definition_type
        if set_default:
            self._default_definition_type = entry_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""
        definition_type_name: str = obj.get(
            "definition_type", self._default_definition_type
        )
        definition_type = self.get_definition_type(definition_type_name)
        definition = definition_type.from_obj(obj)
        self.add_definition(definition)


class BusinessLibrary:
    """A collection of all business definitions."""

    __slots__ = "_definitions", "_definition_types", "_default_definition_type"

    _definitions: dict[str, BusinessDef]
    """Definition instances added to the library."""
    _definition_types: dict[str, Type[BusinessDef]]
    """SettlementDef types for loading data from config files."""
    _default_definition_type: str
    """The default definition type to use when loading from a data dict."""

    def __init__(self, default_definition_type: Type[BusinessDef]) -> None:
        self._definitions = {}
        self._definition_types = {}
        self._default_definition_type = ""
        self.add_definition_type(default_definition_type, set_default=True)

    def get_definition(self, definition_id: str) -> BusinessDef:
        """Get a definition instance from the library."""
        return self._definitions[definition_id]

    def add_definition(self, business_def: BusinessDef) -> None:
        """Add a definition instance to the library."""
        self._definitions[business_def.definition_id] = business_def

    def get_definition_type(self, definition_type_name: str) -> Type[BusinessDef]:
        """Get a definition type."""
        return self._definition_types[definition_type_name]

    def add_definition_type(
        self,
        definition_type: Type[BusinessDef],
        set_default: bool = False,
        alias: str = "",
    ) -> None:
        """Add a definition type for loading objs."""
        entry_key = alias if alias else definition_type.__name__
        self._definition_types[entry_key] = definition_type
        if set_default:
            self._default_definition_type = entry_key

    def add_definition_from_obj(self, obj: dict[str, Any]) -> None:
        """Parse a definition from a dict and add to the library."""
        definition_type_name: str = obj.get(
            "definition_type", self._default_definition_type
        )
        definition_type = self.get_definition_type(definition_type_name)
        definition = definition_type.from_obj(obj)
        self.add_definition(definition)


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
