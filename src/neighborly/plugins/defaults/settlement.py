import os
import pathlib

from neighborly.loaders import load_prefabs
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="default settlement plugin",
    plugin_id="default.create_town",
    version="0.1.0",
)

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"


def setup(sim: Neighborly):
    load_prefabs(sim.world, _RESOURCES_DIR / "town.default.yaml")
