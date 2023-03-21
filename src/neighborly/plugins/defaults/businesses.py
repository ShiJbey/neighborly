import os
import pathlib
from typing import Any

from neighborly.loaders import load_occupation_types, load_prefab
from neighborly.simulation import Neighborly, PluginInfo

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"

plugin_info = PluginInfo(
    name="default businesses plugin",
    plugin_id="default.businesses",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    load_occupation_types(_RESOURCES_DIR / "occupation_types.yaml")

    load_prefab(_RESOURCES_DIR / "business.default.yaml")
    load_prefab(_RESOURCES_DIR / "business.default.library.yaml")
    load_prefab(_RESOURCES_DIR / "business.default.cafe.yaml")
