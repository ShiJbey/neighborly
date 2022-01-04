from typing import Dict, Tuple
import esper

from neighborly.core.character import CharacterConfig, GameCharacter
from neighborly.core.gameobject import GameObject
from neighborly.core.routine import Routine


_character_config_registry: Dict[str, CharacterConfig] = {}


def register_character_config(name: str, config: CharacterConfig) -> None:
    _character_config_registry[name] = config


def create_character(world: esper.World, config_name: str = 'default') -> Tuple[int, GameCharacter]:

    character_id = world.create_entity()

    character = GameCharacter.create(
        config=_character_config_registry[config_name])

    world.add_component(character_id, GameObject(str(character.name)))
    world.add_component(character_id, character)
    world.add_component(character_id, Routine())

    return character_id, character
