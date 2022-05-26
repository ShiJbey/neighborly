"""Utility functions to help users load configuration data from files
"""
import copy
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

import yaml

from neighborly.core.business import BusinessDefinition
from neighborly.core.character import CharacterDefinition
from neighborly.core.engine import (
    ComponentDefinition,
    EntityArchetypeDefinition,
    NeighborlyEngine,
)
from neighborly.core.relationship import RelationshipModifier

logger = logging.getLogger(__name__)

AnyPath = Union[str, Path]


def load_names(
    rule_name: str,
    names: Optional[List[str]] = None,
    filepath: Optional[AnyPath] = None,
) -> None:
    """Load names a list of names from a text file or given list"""
    from neighborly.core.name_generation import register_rule

    if names:
        register_rule(rule_name, names)
    elif filepath:
        with open(filepath, "r") as f:
            register_rule(rule_name, f.read().splitlines())
    else:
        raise ValueError("Need to supply names list or path to file containing names")


class MissingComponentSpecError(Exception):
    """Error raised when an entity archetype is missing an expected component"""

    def __init__(self, component: str) -> None:
        super().__init__(f"Missing spec for component: '{component}'")
        self.message = f"Missing spec for component: '{component}'"

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message


class UnsupportedFileType(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ISectionLoader(Protocol):
    def __call__(self, engine: NeighborlyEngine, data: Any) -> None:
        raise NotImplementedError()


class YamlDataLoader:
    """Load Neighborly Component and Archetype definitions from an YAML"""

    __slots__ = "_raw_data"

    _section_loaders: Dict[str, ISectionLoader] = {}

    def __init__(
        self,
        str_data: Optional[str] = None,
        filepath: Optional[AnyPath] = None,
    ) -> None:
        self._raw_data: Dict[str, Any] = {}

        if str_data:
            self._raw_data = yaml.safe_load(str_data)
        elif filepath:
            with open(filepath, "r") as f:
                self._raw_data = yaml.safe_load(f)
        else:
            raise ValueError("No data string or file path given")

    def load(self, engine: NeighborlyEngine) -> None:
        """
        Load each section of that YAML datafile

        Parameters
        ----------
        engine: NeighborlyEngine
            Neighborly engine instance to load archetype data into
        """
        for section, data in self._raw_data.items():
            if section in self._section_loaders:
                self._section_loaders[section](engine, data)
            else:
                logger.warning(f"skipping unsupported YAML section '{section}'.")

    @classmethod
    def section_loader(cls, section_name: str):
        def decorator(section_loader: ISectionLoader):
            YamlDataLoader._section_loaders[section_name] = section_loader
            return section_loader

        return decorator


@YamlDataLoader.section_loader("CharacterDefinitions")
def _load_character_definitions(
    engine: NeighborlyEngine, data: List[Dict[str, Any]]
) -> None:
    """Process data related to defining activities"""
    for character_def in data:
        CharacterDefinition.register_type(CharacterDefinition(**character_def))


@YamlDataLoader.section_loader("BusinessDefinitions")
def _load_business_definitions(
    engine: NeighborlyEngine, data: List[Dict[str, Any]]
) -> None:
    """Process data related to defining activities"""
    for business_def in data:
        BusinessDefinition.register_type(BusinessDefinition(**business_def))


def _load_entity_archetype(
    engine: NeighborlyEngine, data: Dict[str, Any]
) -> EntityArchetypeDefinition:
    archetype = EntityArchetypeDefinition(
        data["name"],
        is_template=data.get("template", False),
    )

    if archetype["inherits"]:
        parent = engine.get_character_archetype(archetype["inherits"])

        # Copy component specs from the parent
        for component_spec in parent.get_components().values():
            archetype.add_component(copy.deepcopy(component_spec))

    if "components" not in data:
        raise ValueError("Entity spec missing component definitions")

    for component in data["components"]:
        component_name = component["type"]

        options: Dict[str, Any] = component.get("options", {})

        component = archetype.try_component(component_name)
        if component:
            component.update(options)
        else:
            component = ComponentDefinition(component_name, {**options})

        archetype.add_component(component)

    return archetype


@YamlDataLoader.section_loader("Characters")
def _load_character_data(engine: NeighborlyEngine, data: List[Dict[str, Any]]) -> None:
    """Process data related to defining character archetypes"""
    for character in data:
        archetype = _load_entity_archetype(engine, character)

        if (
            archetype.try_component("GameCharacter") is None
            and not archetype.is_template
        ):
            raise MissingComponentSpecError("GameCharacter")

        engine.add_character_archetype(archetype)


@YamlDataLoader.section_loader("Places")
def _load_place_data(engine: NeighborlyEngine, data: List[Dict[str, Any]]) -> None:
    """Process information regarding place archetypes"""
    for place in data:
        archetype = _load_entity_archetype(engine, place)
        engine.add_place_archetype(archetype)


@YamlDataLoader.section_loader("Businesses")
def _load_business_data(engine: NeighborlyEngine, data: List[Dict[str, Any]]) -> None:
    """Process information regarding place archetypes"""
    for business in data:
        archetype = _load_entity_archetype(engine, business)

        if archetype.try_component("Business") is None and not archetype.is_template:
            raise MissingComponentSpecError("Business")

        engine.add_business_archetype(archetype)


@YamlDataLoader.section_loader("Residences")
def _load_residence_data(engine: NeighborlyEngine, data: List[Dict[str, Any]]) -> None:
    """Process information regarding place archetypes"""
    for residence in data:
        archetype = _load_entity_archetype(engine, residence)
        engine.add_residence_archetype(archetype)


@YamlDataLoader.section_loader("RelationshipModifiers")
def _load_relationship_tag_data(
    engine: NeighborlyEngine, data: List[Dict[str, Any]]
) -> None:
    """Load list of dictionary objects defining relationship tags"""
    for modifier in data:
        # Convert the dictionary to an object
        tag = RelationshipModifier(**modifier)
        RelationshipModifier.register_tag(tag)
