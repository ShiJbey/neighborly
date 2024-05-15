"""Built-in plugin with default residence definitions."""

import pathlib

from neighborly.loaders import load_residences
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_plugin(sim: Simulation) -> None:
    """Load plugin data."""

    load_residences(sim, _DATA_DIR / "residences.json")
