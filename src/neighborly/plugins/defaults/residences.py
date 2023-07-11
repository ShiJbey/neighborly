import os
import pathlib

from neighborly.loaders import load_prefabs
from neighborly.simulation import Neighborly, PluginInfo

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"

plugin_info = PluginInfo(
    name="default residences plugin",
    plugin_id="default.residences",
    version="0.1.0",
)


def setup(sim: Neighborly):
    load_prefabs(sim.world, _RESOURCES_DIR / "residence.default.house.yaml")
