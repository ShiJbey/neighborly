"""neighborly.loaders.py

Utility functions for importing simulation data.

"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Union, cast

import yaml
from pydantic import ValidationError

from neighborly.components.activity import register_activity_type
from neighborly.components.business import (
    register_occupation_type,
    register_service_type,
)
from neighborly.components.items import register_item_type
from neighborly.core.ecs import GameObjectPrefab, World
from neighborly.core.tracery import Tracery


def load_occupation_types(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """Load occupation information from a data file.

    Parameters
    ----------
    world
        The world instance.
    file_path
        The path of the data file to load.
    """

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    if isinstance(data, list):
        # That data file contains multiple occupation definitions
        data = cast(List[Dict[str, Any]], data)
        for entry in data:
            try:
                register_occupation_type(world, GameObjectPrefab.parse_obj(entry))
            except ValidationError as ex:
                error_msg = f"Encountered error parsing prefab: {entry['name']}"
                print(error_msg)
                print(str(ex))
    else:
        # The data file contains only a single occupation definition
        register_occupation_type(world, GameObjectPrefab.parse_obj(data))


def load_activities(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """Load activity information from a data file.

    Parameters
    ----------
    world
        The world instance.
    file_path
        The path of the data file to load.
    """

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    if isinstance(data, list):
        # That data file contains multiple occupation definitions
        data = cast(List[Dict[str, Any]], data)
        for entry in data:
            try:
                register_activity_type(world, GameObjectPrefab.parse_obj(entry))
            except ValidationError as ex:
                error_msg = f"Encountered error parsing prefab: {entry['name']}"
                print(error_msg)
                print(str(ex))
    else:
        # The data file contains only a single occupation definition
        register_activity_type(world, GameObjectPrefab.parse_obj(data))


def load_services(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """Load service information from a data file.

    Parameters
    ----------
    world
        The world instance.
    file_path
        The path of the data file to load.
    """

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    if isinstance(data, list):
        # That data file contains multiple occupation definitions
        data = cast(List[Dict[str, Any]], data)
        for entry in data:
            try:
                register_service_type(world, GameObjectPrefab.parse_obj(entry))
            except ValidationError as ex:
                error_msg = f"Encountered error parsing prefab: {entry['name']}"
                print(error_msg)
                print(str(ex))
    else:
        # The data file contains only a single occupation definition
        register_service_type(world, GameObjectPrefab.parse_obj(data))


def load_prefabs(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """Load an entity prefab data from a data file.

    Parameters
    ----------
    world
        The world instance.
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

    if isinstance(data, list):
        # That data file contains multiple occupation definitions
        for entry in data:
            world.gameobject_manager.add_prefab(GameObjectPrefab.parse_obj(entry))
    else:
        # The data file contains only a single occupation definition
        world.gameobject_manager.add_prefab(GameObjectPrefab.parse_obj(data))


def load_names(
    world: World, rule_name: str, file_path: Union[str, pathlib.Path]
) -> None:
    """Load names a list of names from a file and register them in Tracery.

    This function assumes that names are organized one-per-line in a text file.

    Parameters
    ----------
    world
        The world instance.
    rule_name
        The name of the rule to register the names under in Tracery.
    file_path
        The path of the data file to load.
    """
    with open(file_path, "r") as f:
        world.resource_manager.get_resource(Tracery).add_rules(
            {rule_name: f.read().splitlines()}
        )


def load_items(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """Load item information from a data file.

    Parameters
    ----------
    world
        The world instance.
    file_path
        The path of the data file to load.
    """

    path_obj = pathlib.Path(file_path)

    if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
        raise Exception(
            f"Expected YAML or JSON file but file had extension, {path_obj.suffix}"
        )

    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    if isinstance(data, list):
        # That data file contains multiple occupation definitions
        data = cast(List[Dict[str, Any]], data)
        for entry in data:
            try:
                register_item_type(world, GameObjectPrefab.parse_obj(entry))
            except ValidationError as ex:
                error_msg = f"Encountered error parsing prefab: {entry['name']}"
                print(error_msg)
                print(str(ex))
    else:
        # The data file contains only a single occupation definition
        register_item_type(world, GameObjectPrefab.parse_obj(data))
