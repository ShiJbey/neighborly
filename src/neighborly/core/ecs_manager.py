from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import esper

from neighborly.core.business import Business, BusinessConfig
from neighborly.core.character.character import (
    CharacterConfig,
    GameCharacter,
)
from neighborly.core.gameobject import GameObject
from neighborly.core.location import Location
from neighborly.core.routine import Routine
from neighborly.core.name_generation import get_name

_character_config_registry: Dict[str, CharacterConfig] = {}


def register_character_config(name: str, config: CharacterConfig) -> None:
    _character_config_registry[name] = config


def create_character(
    world: esper.World, config_name: str = "default", age_range: str = "adult"
) -> Tuple[int, GameCharacter]:

    character_id = world.create_entity()

    character = GameCharacter.create(
        config=_character_config_registry[config_name], age_range=age_range
    )

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


def register_structure_def(name: str, data: StructureDefinition) -> None:
    """Register a structure definition with the ECS manager"""
    _all_structures[name] = data

    if data.business_definition is not None:
        _business_structures[name] = data

    if data.residence_definition is not None:
        _residential_structures[name] = data


def create_structure(world: esper.World, name: str) -> int:
    structure_def: StructureDefinition = _all_structures[name]

    structure_id = world.create_entity()

    location = Location(structure_def.max_capacity, structure_def.activities)

    if structure_def.name_generator:
        structure_name = get_name(structure_def.name_generator)
    else:
        structure_name = name

    game_object = GameObject(structure_name)

    world.add_component(structure_id, game_object)
    world.add_component(structure_id, location)

    if structure_def.business_definition:
        business = Business(structure_def.business_definition)
        world.add_component(structure_id, business)

    return structure_id
