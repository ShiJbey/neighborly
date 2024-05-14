"""Built-in plugin with default character definitions."""

import pathlib

from neighborly.loaders import load_beliefs, load_characters
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_plugin(sim: Simulation) -> None:
    """Load plugin data."""

    load_characters(sim, _DATA_DIR / "characters.json")
    load_beliefs(sim, _DATA_DIR / "beliefs.json")
