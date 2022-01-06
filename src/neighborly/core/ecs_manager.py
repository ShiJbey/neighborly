from typing import Dict, Tuple, Optional, Callable, List, Any
from dataclasses import dataclass, field

import esper
import yaml

from neighborly.core.character.character import CharacterConfig, GameCharacter, LifeCycleConfig
from neighborly.core.gameobject import GameObject
from neighborly.core.routine import Routine
from neighborly.core.business import BusinessConfig, Business
from neighborly.core.location import Location


_character_config_registry: Dict[str, CharacterConfig] = {}


def register_character_config(name: str, config: CharacterConfig) -> None:
    _character_config_registry[name] = config


@dataclass(frozen=True)
class CharacterDefinition:
    """Settings used to create new character archetypes

    Fields
    ------
    masculine_names: str
        Name of the registered factory that creates instances
        of names that are considered to be more masculine
    feminine_names: str
        Name of the registered factory that creates instances
        of names that are considered to be more feminine
    neutral_names: str
        Name of registered factory that creates instances
        of names that are considered to be more neutral
    surnames: str
        Name of registered factory that creates instances
        of character surnames
    lifecycle: LifeCycleConfig
        Configuration parameters for a characters lifecycle
    components: Dict[str, Dict[str, Any]]
        Dict of additional components and their parameters
        that should be included when constructing the
        character archetype
    """
    masculine_names: str = 'default'
    feminine_names: str = 'default'
    neutral_names: str = 'default'
    surnames: str = 'default'
    lifecycle: LifeCycleConfig = field(default_factory=LifeCycleConfig)
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def create_character(world: esper.World, config_name: str = 'default') -> Tuple[int, GameCharacter]:

    character_id = world.create_entity()

    character = GameCharacter.create(
        config=_character_config_registry[config_name])

    world.add_component(character_id, GameObject(str(character.name)))
    world.add_component(character_id, character)
    world.add_component(character_id, Routine())

    return character_id, character


@dataclass(frozen=True)
class StructureDefinition:
    name: str
    activities: List[str] = field(default_factory=list)
    max_capacity: int = 9999
    name_generator: Optional[str] = None
    business_definition: Optional[BusinessConfig] = None
    residence_definition: Optional[Dict[str, Any]] = None


_all_structures: Dict[str, StructureDefinition] = {}
_business_structures: Dict[str, StructureDefinition] = {}
_residential_structures: Dict[str, StructureDefinition] = {}
_structure_name_generators: Dict[str, Callable[..., str]] = {}


def register_structure_name_generator(name: str, generator: Callable[..., str]) -> None:
    _structure_name_generators[name] = generator


def register_structure_def(name: str, data: StructureDefinition) -> None:
    """Register a structure definition with the ECS manager"""
    _all_structures[name] = data

    # Detect if it is a residence or business
    if data.business_definition is not None:
        _business_structures[name] = data

    if data.residence_definition is not None:
        _residential_structures[name] = data


def create_structure(world: esper.World, name: str) -> int:
    structure_def: StructureDefinition = _all_structures[name]

    structure_id = world.create_entity()

    location = Location(structure_def.max_capacity, structure_def.activities)

    if structure_def.name_generator:
        structure_name = _structure_name_generators[structure_def.name_generator](
        )
    else:
        structure_name = name

    game_object = GameObject(structure_name)

    world.add_component(structure_id, game_object)
    world.add_component(structure_id, location)

    if structure_def.business_definition:
        business = Business(structure_def.business_definition)
        world.add_component(structure_id, business)

    return structure_id
