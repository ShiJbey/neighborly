import os
from pathlib import Path

from neighborly.core.engine import NeighborlyEngine
from neighborly.loaders import load_names, YamlDataLoader

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


def initialize_plugin(engine: NeighborlyEngine) -> None:
    # Load character name data
    load_names("last_name", filepath=_RESOURCES_DIR / "names" / "surnames.txt")
    load_names("first_name", filepath=_RESOURCES_DIR / "names" / "neutral_names.txt")
    load_names(
        "feminine_first_name", filepath=_RESOURCES_DIR / "names" / "feminine_names.txt"
    )
    load_names(
        "masculine_first_name",
        filepath=_RESOURCES_DIR / "names" / "masculine_names.txt",
    )

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

    YamlDataLoader(filepath=_RESOURCES_DIR / "data.yaml").load(engine)
