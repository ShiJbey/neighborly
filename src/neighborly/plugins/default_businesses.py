"""Built-in plugin with default business and job role definitions."""

import pathlib

from neighborly.loaders import load_businesses, load_job_roles
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_plugin(sim: Simulation) -> None:
    """Load plugin data."""

    load_businesses(sim, _DATA_DIR / "businesses.json")
    load_job_roles(sim, _DATA_DIR / "job_roles.json")
