import os
from pathlib import Path

from neighborly.loaders import (
    load_activity_definitions,
    load_names,
    load_occupation_definitions,
    load_structure_definitions,
)

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent.parent / "data"


def initialize_plugin() -> None:
    # Load character name data
    load_names("surname", filepath=_RESOURCES_DIR / "names" / "surnames.txt")
    load_names("first_name", filepath=_RESOURCES_DIR / "names" / "neutral_names.txt")
    load_names(
        "feminine_first_name", filepath=_RESOURCES_DIR / "names" / "feminine_names.txt"
    )
    load_names(
        "masculine_first_name",
        filepath=_RESOURCES_DIR / "names" / "masculine_names.txt",
    )

    # Load definitions for types of activities that exist
    load_activity_definitions(filepath=_RESOURCES_DIR / "activities.yaml")

    # Load the types of occupations that exist
    load_occupation_definitions(filepath=_RESOURCES_DIR / "occupations.yaml")

    # Load potential names for different structures in the town
    load_names(
        "restaurant_name", filepath=_RESOURCES_DIR / "names" / "restaurant_names.txt"
    )
    load_names("bar_name", filepath=_RESOURCES_DIR / "names" / "bar_names.txt")

    # Load potential names for the town
    load_names(
        "town_name",
        filepath=_RESOURCES_DIR / "names" / "US_settlement_names.txt",
    )

    # Load structure definitions from YAML
    load_structure_definitions(filepath=_RESOURCES_DIR / "businesses.yaml")
    load_structure_definitions(filepath=_RESOURCES_DIR / "residences.yaml")
    load_structure_definitions(filepath=_RESOURCES_DIR / "other_places.yaml")
