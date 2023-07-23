import os
import pathlib

from neighborly.loaders import NeighborlyDataLoader
from neighborly.simulation import Neighborly, PluginInfo

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"

plugin_info = PluginInfo(
    name="default characters plugin",
    plugin_id="default.characters",
    version="0.1.0",
)


def setup(sim: Neighborly):
    NeighborlyDataLoader.load_file(sim.world, _RESOURCES_DIR / "characters.default.yaml")
