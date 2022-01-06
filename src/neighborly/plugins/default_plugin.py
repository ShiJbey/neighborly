import os
from pathlib import Path

from neighborly.authoring import load_activity_definitions, load_structure_definitions, \
    load_town_names, load_structure_names, load_occupation_definitions, \
    load_surnames, load_feminine_names, load_masculine_names, load_neutral_names


_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent.parent / 'data'


def initialize_plugin() -> None:
    # Load character name data
    load_surnames(
        'default', filepath=_RESOURCES_DIR / 'names' / 'surnames.txt')
    load_neutral_names(
        'default', filepath=_RESOURCES_DIR / 'names' / 'neutral_names.txt')
    load_feminine_names(
        'default', filepath=_RESOURCES_DIR / 'names' / 'feminine_names.txt')
    load_masculine_names(
        'default', filepath=_RESOURCES_DIR / 'names' / 'masculine_names.txt')

    # Load definitions for types of activities that exist
    load_activity_definitions(
        filepath=_RESOURCES_DIR / 'activities.yaml')

    # Load the types of occupations that exist
    load_occupation_definitions(
        filepath=_RESOURCES_DIR / 'occupations.yaml')

    # Load potential names for different structures in the town
    load_structure_names(
        'default',
        filepath=_RESOURCES_DIR / 'names' / 'masculine_names.txt')

    # Load potential names for the town
    load_town_names(
        'default',
        filepath=_RESOURCES_DIR / 'names' / 'US_settlement_names.txt')

    # Load structure definitions from YAML
    load_structure_definitions(
        filepath=_RESOURCES_DIR / 'businesses.yaml')
    load_structure_definitions(
        filepath=_RESOURCES_DIR / 'residences.yaml')
    load_structure_definitions(
        filepath=_RESOURCES_DIR / 'other_places.yaml')
