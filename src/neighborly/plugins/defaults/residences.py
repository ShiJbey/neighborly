import os
import pathlib
from typing import Any

from neighborly.loaders import load_prefab
from neighborly.simulation import Neighborly, PluginInfo

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"

plugin_info = PluginInfo(
    name="default residences plugin",
    plugin_id="default.residences",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    load_prefab(_RESOURCES_DIR / "residence.default.house.yaml")
