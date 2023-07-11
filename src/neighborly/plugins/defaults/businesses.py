import os
import pathlib

from neighborly.loaders import load_prefabs
from neighborly.plugins.defaults.occupations import Barista, Librarian, Owner
from neighborly.simulation import Neighborly, PluginInfo

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"

plugin_info = PluginInfo(
    name="default businesses plugin",
    plugin_id="default.businesses",
    version="0.1.0",
)


def setup(sim: Neighborly):
    sim.world.gameobject_manager.register_component(Librarian)
    sim.world.gameobject_manager.register_component(Owner)
    sim.world.gameobject_manager.register_component(Barista)
    
    load_prefabs(sim.world, _RESOURCES_DIR / "business.default.yaml")
    load_prefabs(sim.world, _RESOURCES_DIR / "business.default.library.yaml")
    load_prefabs(sim.world, _RESOURCES_DIR / "business.default.cafe.yaml")
