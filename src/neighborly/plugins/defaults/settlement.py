import os
import pathlib
from typing import Any

from neighborly.loaders import load_prefab
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="default settlement plugin",
    plugin_id="default.create_town",
    version="0.1.0",
)

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"


def setup(sim: Neighborly, **kwargs: Any):
    load_prefab(_RESOURCES_DIR / "town.default.yaml")
