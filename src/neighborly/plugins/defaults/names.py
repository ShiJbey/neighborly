import os
import pathlib

from neighborly.simulation import Neighborly, PluginInfo
from neighborly.tracery import load_names

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"

plugin_info = PluginInfo(
    name="default names plugin",
    plugin_id="default.names",
    version="0.1.0",
)


def setup(sim: Neighborly):
    load_names(
        sim.world,
        rule_name="character::last_name",
        file_path=_RESOURCES_DIR / "names" / "surnames.txt",
    )

    load_names(
        sim.world,
        rule_name="character::first_name::NonBinary",
        file_path=_RESOURCES_DIR / "names" / "neutral_names.txt",
    )

    load_names(
        sim.world,
        rule_name="character::first_name::Female",
        file_path=_RESOURCES_DIR / "names" / "feminine_names.txt",
    )

    load_names(
        sim.world,
        rule_name="character::first_name::Male",
        file_path=_RESOURCES_DIR / "names" / "masculine_names.txt",
    )

    load_names(
        sim.world,
        rule_name="restaurant_name",
        file_path=_RESOURCES_DIR / "names" / "restaurant_names.txt",
    )

    load_names(
        sim.world,
        rule_name="bar_name",
        file_path=_RESOURCES_DIR / "names" / "bar_names.txt",
    )

    load_names(
        sim.world,
        rule_name="settlement_name",
        file_path=_RESOURCES_DIR / "names" / "US_settlement_names.txt",
    )
