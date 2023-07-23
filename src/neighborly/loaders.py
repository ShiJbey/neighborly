"""neighborly.loaders.py

Utility functions for importing simulation data.

"""
from __future__ import annotations

import logging
import pathlib
from abc import abstractmethod
from collections import defaultdict
from typing import Any, ClassVar, DefaultDict, Dict, List, Protocol, Union

import yaml

from neighborly.components.character import register_character_prefab
from neighborly.components.items import register_item_type
from neighborly.components.residence import register_residence_prefab
from neighborly.core.ecs import GameObjectPrefab, World
from neighborly.core.tracery import Tracery

_logger = logging.getLogger(__name__)


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


def load_prefabs_from_file(file_path: Union[str, pathlib.Path]) -> List[GameObjectPrefab]:
    """Loads one or more GameObject prefabs from a data file.

    Parameters
    ----------
    file_path
        The path of the data file to load.

    Returns
    -------
    List[GameObjectPrefab]
        The prefabs contained in the file
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
        return [
            GameObjectPrefab.parse_obj(entry)
            for entry in data
        ]
    else:
        # The data file contains only a single occupation definition
        return [GameObjectPrefab.parse_obj(data)]


class DataSectionLoader(Protocol):
    """Functions responsible for loading sections of a neighborly data file."""

    @abstractmethod
    def __call__(self, world: World, data: Any) -> None:
        raise NotImplementedError


class NeighborlyDataLoader:
    """Loads data into a world instance from Neighborly data files."""

    _section_loaders: ClassVar[DefaultDict[str, List[DataSectionLoader]]] = defaultdict(list)

    @classmethod
    def add_section_loader(cls, section_name: str, section_loader: DataSectionLoader) -> None:
        cls._section_loaders[section_name].append(section_loader)

    @classmethod
    def load_file(cls, world: World, file_path: Union[str, pathlib.Path]) -> None:

        path_obj = pathlib.Path(file_path)

        if path_obj.suffix.lower() not in (".yaml", ".yml", ".json"):
            raise Exception(
                f"Expected YAML or JSON file but file had extension, {path_obj.suffix}."
            )

        with open(file_path, "r") as f:
            file_data: Dict[str, Any] = yaml.safe_load(f)

            for section_header, section_data in file_data.items():
                for section_loader in cls._section_loaders[section_header]:
                    section_loader(world, section_data)


def _load_character_data_section(world: World, data: List[Dict[str, Any]]) -> None:
    for entry in data:
        register_character_prefab(world, GameObjectPrefab.from_raw(entry))


def _load_business_data_section(world: World, data: List[Dict[str, Any]]) -> None:
    for entry in data:
        register_character_prefab(world, GameObjectPrefab.from_raw(entry))


def _load_residence_data_section(world: World, data: List[Dict[str, Any]]) -> None:
    for entry in data:
        register_residence_prefab(world, GameObjectPrefab.from_raw(entry))


def _load_items_data_section(world: World, data: List[Dict[str, Any]]) -> None:
    for entry in data:
        register_item_type(world, GameObjectPrefab.from_raw(entry))


NeighborlyDataLoader.add_section_loader(
    "Characters",
    _load_character_data_section
)

NeighborlyDataLoader.add_section_loader(
    "Businesses",
    _load_business_data_section
)

NeighborlyDataLoader.add_section_loader(
    "Residences",
    _load_residence_data_section
)

NeighborlyDataLoader.add_section_loader(
    "Items",
    _load_items_data_section
)
