"""
neighborly/loaders.py

Utility class and functions for importing simulation configuration data
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Union

import yaml

from neighborly.components.business import OccupationType, OccupationTypes
from neighborly.core.ecs import EntityPrefab, GameObjectFactory
from neighborly.core.tracery import Tracery


def load_occupation_types(file_path: Union[str, pathlib.Path]) -> None:
    """Load occupation information from a data file.

    Parameters
    ----------
    file_path
        The path of the data file to load.
    """

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    with open(file_path, "r") as f:
        data: List[Dict[str, Any]] = yaml.safe_load(f)

    for entry in data:
        OccupationTypes.add(
            OccupationType(
                name=entry["name"],
                level=entry.get("level", 1),
            )
        )


def load_prefab(file_path: Union[str, pathlib.Path]) -> None:
    """Load a single entity prefab from a data file.

    Parameters
    ----------
    file_path
        The path of the data file to load.
    """

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    with open(file_path, "r") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    GameObjectFactory.add(EntityPrefab.parse_obj(data))


def load_names(rule_name: str, file_path: Union[str, pathlib.Path]) -> None:
    """Load names a list of names from a file and register them in Tracery.

    This function assumes that names are organized one-per-line in a text file.

    Parameters
    ----------
    rule_name
        The name of the rule to register the names under in Tracery.
    file_path
        The path of the data file to load.
    """
    with open(file_path, "r") as f:
        Tracery.add_rules({rule_name: f.read().splitlines()})


def load_data_file(file_path: Union[str, pathlib.Path]) -> None:
    """Load various data from a single file.

    This function can load multiple prefabs, and occupation types from a single file. It
    assumes that the data is separated into sections like "Prefabs" and "Occupations".

    Parameters
    ----------
    file_path
        The path of the data file to load.
    """

    with open(file_path, "r") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    character_data: List[Dict[str, Any]] = data.get("Characters", [])
    for entry in character_data:
        GameObjectFactory.add(EntityPrefab.parse_obj(entry))

    business_data: List[Dict[str, Any]] = data.get("Businesses", [])
    for entry in business_data:
        GameObjectFactory.add(EntityPrefab.parse_obj(entry))

    residence_data: List[Dict[str, Any]] = data.get("Residences", [])
    for entry in residence_data:
        GameObjectFactory.add(EntityPrefab.parse_obj(entry))

    prefab_data: List[Dict[str, Any]] = data.get("Prefabs", [])
    for entry in prefab_data:
        GameObjectFactory.add(EntityPrefab.parse_obj(entry))

    occupation_defs: List[Dict[str, Any]] = data.get("Occupations", [])
    for entry in occupation_defs:
        OccupationTypes.add(
            OccupationType(
                name=entry["name"],
                level=entry.get("level", 1),
            )
        )

    name_data: List[Dict[str, Any]] = data.get("Names", [])
    for entry in name_data:
        load_names(entry["rule"], entry["path"])
