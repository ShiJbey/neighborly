"""Loads a default set of traits.

"""

import pathlib

from neighborly.loaders import load_location_preferences, load_beliefs, load_traits
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_plugin(sim: Simulation) -> None:
    """Load the plugin's content."""

    load_beliefs(sim, _DATA_DIR / "beliefs.json")
    load_location_preferences(sim, _DATA_DIR / "location_preferences.json")
    load_traits(sim, _DATA_DIR / "traits.json")
