"""
neighborly/loaders.py

Utility class and functions for importing simulation configuration data
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Union

import yaml

from neighborly.components.business import OccupationType
from neighborly.content_management import (
    BusinessLibrary,
    CharacterLibrary,
    OccupationTypeLibrary,
    ResidenceLibrary,
)
from neighborly.core.ecs import World
from neighborly.core.tracery import Tracery
from neighborly.prefabs import BusinessPrefab, CharacterPrefab, ResidencePrefab
from neighborly.simulation import Neighborly
from neighborly.utils.common import deep_merge


def load_occupation_types(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """Load virtue mappings for activities"""

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    with open(file_path, "r") as f:
        data: List[Dict[str, Any]] = yaml.safe_load(f)

    library = world.get_resource(OccupationTypeLibrary)

    for entry in data:
        library.add(
            OccupationType(
                name=entry["name"],
                level=entry.get("level", 1),
            )
        )


def load_character_prefab(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """loads a CharacterEntityPrefab from a yaml file"""

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    library = world.get_resource(CharacterLibrary)

    with open(file_path, "r") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    base_data: Dict[str, Any] = dict()

    data["is_template"] = data.get("is_template", False)

    if base_prefab_name := data.get("extends", ""):
        base_data = library.get(base_prefab_name).dict()

    full_prefab_data = deep_merge(base_data, data)

    new_prefab = CharacterPrefab.parse_obj(full_prefab_data)

    library.add(new_prefab)


def load_business_prefab(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """loads a CharacterEntityPrefab from a yaml file"""

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    library = world.get_resource(BusinessLibrary)

    with open(file_path, "r") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    base_data: Dict[str, Any] = dict()

    data["is_template"] = data.get("is_template", False)

    if base_prefab_name := data.get("extends", ""):
        base_data = library.get(base_prefab_name).dict()

    full_prefab_data = deep_merge(base_data, data)

    new_prefab = BusinessPrefab.parse_obj(full_prefab_data)

    library.add(new_prefab)


def load_residence_prefab(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """loads a CharacterEntityPrefab from a yaml file"""

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    library = world.get_resource(ResidenceLibrary)

    with open(file_path, "r") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    base_data: Dict[str, Any] = dict()

    data["is_template"] = data.get("is_template", False)

    if base_prefab_name := data.get("extends", ""):
        base_data = library.get(base_prefab_name).dict()

    full_prefab_data = deep_merge(base_data, data)

    new_prefab = ResidencePrefab.parse_obj(full_prefab_data)

    library.add(new_prefab)


def load_names(
    world: World, rule_name: str, filepath: Union[str, pathlib.Path]
) -> None:
    """Load names a list of names from a text file or given list"""
    tracery_instance = world.get_resource(Tracery)

    with open(filepath, "r") as f:
        tracery_instance.add({rule_name: f.read().splitlines()})


def load_data_file(sim: Neighborly, file_path: Union[str, pathlib.Path]) -> None:
    """Load all the fields from the datafile into their respective libraries"""

    with open(file_path, "r") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    character_library = sim.world.get_resource(CharacterLibrary)
    character_defs: List[Dict[str, Any]] = data.get("Characters", [])
    for entry in character_defs:
        base_data: Dict[str, Any] = dict()

        entry["is_template"] = entry.get("is_template", False)

        if base_prefab_name := entry.get("extends", ""):
            base_data = character_library.get(base_prefab_name).dict()

        full_prefab_data = deep_merge(base_data, entry)

        new_prefab = CharacterPrefab.parse_obj(full_prefab_data)

        character_library.add(new_prefab)

    business_library = sim.world.get_resource(BusinessLibrary)
    business_defs: List[Dict[str, Any]] = data.get("Businesses", [])
    for entry in business_defs:
        base_data: Dict[str, Any] = dict()

        entry["is_template"] = entry.get("is_template", False)

        if base_prefab_name := entry.get("extends", ""):
            base_data = business_library.get(base_prefab_name).dict()

        full_prefab_data = deep_merge(base_data, entry)

        new_prefab = BusinessPrefab.parse_obj(full_prefab_data)

        business_library.add(new_prefab)

    residence_library = sim.world.get_resource(ResidenceLibrary)
    residence_defs: List[Dict[str, Any]] = data.get("Residences", [])
    for entry in residence_defs:
        base_data: Dict[str, Any] = dict()

        entry["is_template"] = entry.get("is_template", False)

        if base_prefab_name := entry.get("extends", ""):
            base_data = residence_library.get(base_prefab_name).dict()

        full_prefab_data = deep_merge(base_data, entry)

        new_prefab = ResidencePrefab.parse_obj(full_prefab_data)

        residence_library.add(new_prefab)

    occupation_library = sim.world.get_resource(OccupationTypeLibrary)
    occupation_defs: List[Dict[str, Any]] = data.get("Occupations", [])
    for entry in occupation_defs:
        occupation_library.add(
            OccupationType(
                name=entry["name"],
                level=entry.get("level", 1),
            )
        )

    name_data: List[Dict[str, Any]] = data.get("Names", [])
    for entry in name_data:
        load_names(sim.world, entry["rule"], entry["path"])
