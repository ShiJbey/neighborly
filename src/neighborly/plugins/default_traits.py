"""Loads a default set of traits.

"""

import pathlib

from neighborly.loaders import load_traits
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_plugin(sim: Simulation) -> None:
    """Load the plugin's content."""

    load_traits(sim, _DATA_DIR / "traits.json")
    load_traits(sim, _DATA_DIR / "business_traits.json")
    load_traits(sim, _DATA_DIR / "relationship_traits.json")
