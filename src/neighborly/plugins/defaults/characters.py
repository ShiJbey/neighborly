import os
import pathlib
from typing import Any

from neighborly.loaders import load_character_prefab
from neighborly.simulation import Neighborly, PluginInfo

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"


plugin_info = PluginInfo(
    name="default characters plugin",
    plugin_id="default.characters",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    load_character_prefab(sim.world, _RESOURCES_DIR / "character.default.yaml")
    load_character_prefab(sim.world, _RESOURCES_DIR / "character.default.male.yaml")
    load_character_prefab(sim.world, _RESOURCES_DIR / "character.default.female.yaml")
    load_character_prefab(
        sim.world, _RESOURCES_DIR / "character.default.non-binary.yaml"
    )
