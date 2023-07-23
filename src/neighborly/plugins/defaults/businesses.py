import os
import pathlib

from neighborly.components.business import register_occupation_type
from neighborly.loaders import NeighborlyDataLoader
from neighborly.plugins.defaults.occupations import Barista, Librarian, Owner
from neighborly.simulation import Neighborly, PluginInfo

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"

plugin_info = PluginInfo(
    name="default businesses plugin",
    plugin_id="default.businesses",
    version="0.1.0",
)


def setup(sim: Neighborly):
    register_occupation_type(sim.world, Librarian)
    register_occupation_type(sim.world, Owner)
    register_occupation_type(sim.world, Barista)

    NeighborlyDataLoader.load_file(sim.world, _RESOURCES_DIR / "businesses.default.yaml")
