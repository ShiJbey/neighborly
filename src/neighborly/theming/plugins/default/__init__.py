import os
from pathlib import Path

from neighborly.core.character import GameCharacter, DefaultCharacterNameFactory

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / 'data'


def initialize_plugin() -> None:
    GameCharacter.register_name_factory(
        True,
        'default',
        DefaultCharacterNameFactory(
            _RESOURCES_DIR / 'masculine_names.txt',
            _RESOURCES_DIR / 'surnames.txt'))

    GameCharacter.register_name_factory(
        False,
        'default',
        DefaultCharacterNameFactory(
            _RESOURCES_DIR / 'feminine_names.txt',
            _RESOURCES_DIR / 'surnames.txt'))
