"""Utility functions to help users load configuration data from files
"""
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, List

import yaml

from neighborly.core.town.town import Town
from neighborly.core.activity import register_activity, Activity
from neighborly.core.character.character import GameCharacter, Gender
from neighborly.core.business import BusinessConfig
from neighborly.core.ecs_manager import StructureDefinition, register_structure_def, register_structure_name_generator
from neighborly.core.utils import DefaultNameGenerator

AnyPath = Union[str, Path]


def load_town_names(namespace: str, names: Optional[List[str]] = None, filepath: Optional[AnyPath] = None) -> None:
    """Load town names from a list or text file"""
    Town.register_name_factory(
        namespace, DefaultNameGenerator(names, filepath))


def load_activity_definitions(yaml_str: Optional[str] = None, filepath: Optional[AnyPath] = None) -> None:
    """Loads new activity types from given YAML data"""
    if yaml_str and filepath:
        raise ValueError("Only supply YAML string or file path not both")

    if yaml_str:
        yaml_data: Dict[str, Dict[str, Any]] = yaml.safe_load(yaml_str)
    elif filepath:
        with open(filepath, 'r') as f:
            yaml_data: Dict[str, Dict[str, Any]] = yaml.safe_load(f)
    else:
        raise ValueError("No YAML string or file path given")

    for name, data in yaml_data.items():
        register_activity(Activity(name, tuple(data['traits'])))


def load_structure_definitions(yaml_str: Optional[str] = None, filepath: Optional[AnyPath] = None) -> None:
    if yaml_str and filepath:
        raise ValueError("Only supply YAML string or file path not both")

    if yaml_str:
        structures_raw: Dict[str, Dict[str, Any]] = yaml.safe_load(yaml_str)
    elif filepath:
        with open(filepath, 'r') as f:
            structures_raw: Dict[str, Dict[str, Any]] = yaml.safe_load(f)
    else:
        raise ValueError("No YAML string or file path given")

    # HElPER FUNCTIONS
    def _get_business_config(data: Dict[str, Any], **kwargs) -> Optional[BusinessConfig]:
        config: Optional[Dict[str, Any]] = data.get('business')

        if config is None:
            return

        return BusinessConfig(**kwargs, **config)
    # END HELPER FUNCTIONS

    for name, data in structures_raw.items():
        register_structure_def(name, StructureDefinition(
            name=name,
            activities=data.get('activities', []),
            max_capacity=data.get('max capacity', 9999),
            name_generator=data.get('name generator'),
            business_definition=_get_business_config(data, business_type=name)
        ))


def load_structure_names(namespace: str, names: Optional[List[str]] = None, filepath: Optional[AnyPath] = None) -> None:
    """Load potential structure names from a list of strings or a file"""
    register_structure_name_generator(
        namespace, DefaultNameGenerator(names, filepath))


def load_occupation_definitions(yaml_str: Optional[str] = None, filepath: Optional[AnyPath] = None) -> None:
    """Load occupation types from YAML string or YAML file"""
    ...


def load_surnames(namespace: str,  names: Optional[List[str]] = None, filepath: Optional[AnyPath] = None) -> None:
    """Load names to be used as characters' surnames"""
    GameCharacter.register_surname_factory(
        DefaultNameGenerator(names, filepath),
        name=namespace)


def load_neutral_names(namespace: str,  names: Optional[List[str]] = None, filepath: Optional[AnyPath] = None) -> None:
    """Load names to be used as characters' surnames"""
    GameCharacter.register_firstname_factory(
        DefaultNameGenerator(names, filepath),
        name=namespace)


def load_feminine_names(namespace: str,  names: Optional[List[str]] = None, filepath: Optional[AnyPath] = None) -> None:
    """Load names to be used as characters' surnames"""
    GameCharacter.register_firstname_factory(
        DefaultNameGenerator(names, filepath),
        gender=Gender.FEMININE,
        name=namespace)


def load_masculine_names(namespace: str,  names: Optional[List[str]] = None, filepath: Optional[AnyPath] = None) -> None:
    """Load names to be used as characters' surnames"""
    GameCharacter.register_firstname_factory(
        DefaultNameGenerator(names, filepath),
        gender=Gender.MASCULINE,
        name=namespace)
