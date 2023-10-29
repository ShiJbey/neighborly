"""Loads a default set of names for settlements.

"""

import pathlib

from neighborly.loaders import load_tracery
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_plugin(sim: Simulation) -> None:
    """Load the plugin's content."""

    load_tracery(sim, _DATA_DIR / "settlement_names.tracery.json")
