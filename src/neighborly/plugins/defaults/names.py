import os
import pathlib
from typing import Any

from neighborly.core.name_generation import TraceryNameFactory
from neighborly.simulation import Plugin, Simulation

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent / "data"


class DefaultNameDataPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs: Any) -> None:
        # Load entity name data
        name_generator = sim.world.get_resource(TraceryNameFactory)

        name_generator.load_names(
            rule_name="family_name", filepath=_RESOURCES_DIR / "names" / "surnames.txt"
        )

        name_generator.load_names(
            rule_name="first_name",
            filepath=_RESOURCES_DIR / "names" / "neutral_names.txt",
        )

        name_generator.load_names(
            rule_name="feminine_first_name",
            filepath=_RESOURCES_DIR / "names" / "feminine_names.txt",
        )

        name_generator.load_names(
            rule_name="masculine_first_name",
            filepath=_RESOURCES_DIR / "names" / "masculine_names.txt",
        )

        # Load potential names for different structures in the town
        name_generator.load_names(
            rule_name="restaurant_name",
            filepath=_RESOURCES_DIR / "names" / "restaurant_names.txt",
        )

        name_generator.load_names(
            rule_name="bar_name", filepath=_RESOURCES_DIR / "names" / "bar_names.txt"
        )

        # Load potential names for the town
        name_generator.load_names(
            rule_name="town_name",
            filepath=_RESOURCES_DIR / "names" / "US_settlement_names.txt",
        )


def get_plugin() -> Plugin:
    return DefaultNameDataPlugin()
