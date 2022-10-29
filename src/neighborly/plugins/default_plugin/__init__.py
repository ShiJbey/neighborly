import os
from pathlib import Path

from neighborly.builtin.events import (
    become_enemies_event,
    become_friends_event,
    dating_break_up_event,
    depart_due_to_unemployment,
    die_of_old_age,
    divorce_event,
    find_own_place_event,
    go_out_of_business_event,
    marriage_event,
    pregnancy_event,
    retire_event,
    start_dating_event,
)
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvents
from neighborly.simulation import Plugin, Simulation

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


class DefaultNameDataPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        self.initialize_tracery_name_factory(sim.engine)

    def initialize_tracery_name_factory(self, engine: NeighborlyEngine) -> None:
        # Load entity name data
        engine.name_generator.load_names(
            rule_name="family_name", filepath=_RESOURCES_DIR / "names" / "surnames.txt"
        )
        engine.name_generator.load_names(
            rule_name="first_name",
            filepath=_RESOURCES_DIR / "names" / "neutral_names.txt",
        )
        engine.name_generator.load_names(
            rule_name="feminine_first_name",
            filepath=_RESOURCES_DIR / "names" / "feminine_names.txt",
        )
        engine.name_generator.load_names(
            rule_name="masculine_first_name",
            filepath=_RESOURCES_DIR / "names" / "masculine_names.txt",
        )

        # Load potential names for different structures in the town
        engine.name_generator.load_names(
            rule_name="restaurant_name",
            filepath=_RESOURCES_DIR / "names" / "restaurant_names.txt",
        )
        engine.name_generator.load_names(
            rule_name="bar_name", filepath=_RESOURCES_DIR / "names" / "bar_names.txt"
        )

        # Load potential names for the town
        engine.name_generator.load_names(
            rule_name="town_name",
            filepath=_RESOURCES_DIR / "names" / "US_settlement_names.txt",
        )


class DefaultLifeEventPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        # LifeEvents.add(marriage_event())
        # LifeEvents.add(become_friends_event())
        # LifeEvents.add(become_enemies_event())
        # LifeEvents.add(start_dating_event())
        # LifeEvents.add(dating_break_up_event())
        # LifeEvents.add(divorce_event())
        LifeEvents.add(pregnancy_event())
        LifeEvents.add(retire_event())
        LifeEvents.add(find_own_place_event())
        LifeEvents.add(die_of_old_age())
        LifeEvents.add(go_out_of_business_event())


class DefaultPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        name_data_plugin = DefaultNameDataPlugin()
        life_event_plugin = DefaultLifeEventPlugin()

        name_data_plugin.setup(sim, **kwargs)
        life_event_plugin.setup(sim, **kwargs)


def get_plugin() -> Plugin:
    return DefaultPlugin()
