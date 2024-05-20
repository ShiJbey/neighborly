"""Built-in plugin with default settlement and district definitions."""

import pathlib

from neighborly.loaders import load_districts, load_settlements
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_plugin(sim: Simulation) -> None:
    """Load plugin data."""

    load_settlements(sim, _DATA_DIR / "settlements.json")
    load_districts(sim, _DATA_DIR / "districts.json")
