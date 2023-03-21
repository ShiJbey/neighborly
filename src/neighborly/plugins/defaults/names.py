import os
import pathlib
from typing import Any

from neighborly.loaders import load_names
from neighborly.simulation import Neighborly, PluginInfo

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"


plugin_info = PluginInfo(
    name="default names plugin",
    plugin_id="default.names",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    load_names(
        rule_name="character::default::last_name",
        file_path=_RESOURCES_DIR / "names" / "surnames.txt",
    )

    load_names(
        rule_name="character::default::first_name::gender-neutral",
        file_path=_RESOURCES_DIR / "names" / "neutral_names.txt",
    )

    load_names(
        rule_name="character::default::first_name::feminine",
        file_path=_RESOURCES_DIR / "names" / "feminine_names.txt",
    )

    load_names(
        rule_name="character::default::first_name::masculine",
        file_path=_RESOURCES_DIR / "names" / "masculine_names.txt",
    )

    load_names(
        rule_name="restaurant_name",
        file_path=_RESOURCES_DIR / "names" / "restaurant_names.txt",
    )

    load_names(
        rule_name="bar_name",
        file_path=_RESOURCES_DIR / "names" / "bar_names.txt",
    )

    load_names(
        rule_name="settlement_name",
        file_path=_RESOURCES_DIR / "names" / "US_settlement_names.txt",
    )
