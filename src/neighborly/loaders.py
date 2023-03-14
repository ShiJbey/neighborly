"""
neighborly/loaders.py

Utility class and functions for importing simulation configuration data
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Union

import yaml

from neighborly.components.business import OccupationType
from neighborly.content_management import OccupationTypeLibrary
from neighborly.core.ecs import EntityPrefab, GameObjectFactory, World
from neighborly.core.tracery import Tracery
from neighborly.simulation import Neighborly


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


def load_prefab(file_path: Union[str, pathlib.Path]) -> None:
    """loads a Prefab from a yaml file"""

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    with open(file_path, "r") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    GameObjectFactory.add(EntityPrefab.parse_obj(data))


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

    character_defs: List[Dict[str, Any]] = data.get("Characters", [])
    for entry in character_defs:
        GameObjectFactory.add(EntityPrefab.parse_obj(entry))

    business_defs: List[Dict[str, Any]] = data.get("Businesses", [])
    for entry in business_defs:
        GameObjectFactory.add(EntityPrefab.parse_obj(entry))

    residence_defs: List[Dict[str, Any]] = data.get("Residences", [])
    for entry in residence_defs:
        GameObjectFactory.add(EntityPrefab.parse_obj(entry))

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
