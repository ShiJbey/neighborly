import os
from pathlib import Path

from neighborly.builtin.events import (
    become_enemies_event,
    become_friends_event,
    dating_break_up_event,
    death_event,
    depart_due_to_unemployment,
    die_of_old_age,
    divorce_event,
    find_own_place_event,
    marriage_event,
    pregnancy_event,
    retire_event,
    start_dating_event,
)
from neighborly.core.business import ServiceTypeLibrary
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEventLibrary
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
        # LifeEventLibrary.add(marriage_event())
        # LifeEvents.register(become_friends_event())
        # LifeEvents.register(become_enemies_event())
        # LifeEventLibrary.add(start_dating_event())
        # LifeEventLibrary.add(dating_break_up_event())
        # LifeEventLibrary.add(divorce_event())
        # LifeEventLibrary.add(pregnancy_event())
        # LifeEventLibrary.add(depart_due_to_unemployment())
        LifeEventLibrary.add(retire_event())
        # LifeEventLibrary.add(find_own_place_event())
        LifeEventLibrary.add(die_of_old_age())


class DefaultServicesPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        ServiceTypeLibrary.add_service_type("Drinking")
        ServiceTypeLibrary.add_service_type("Banking")
        ServiceTypeLibrary.add_service_type("College Education")
        ServiceTypeLibrary.add_service_type("Construction")
        ServiceTypeLibrary.add_service_type("Cosmetics")
        ServiceTypeLibrary.add_service_type("Clothing")
        ServiceTypeLibrary.add_service_type("Fire Emergency")
        ServiceTypeLibrary.add_service_type("Food")
        ServiceTypeLibrary.add_service_type("Hardware")
        ServiceTypeLibrary.add_service_type("Errands")
        ServiceTypeLibrary.add_service_type("Socializing")
        ServiceTypeLibrary.add_service_type("Shopping")
        ServiceTypeLibrary.add_service_type("Secondary Education")
        ServiceTypeLibrary.add_service_type("Realty")
        ServiceTypeLibrary.add_service_type("Public Service")
        ServiceTypeLibrary.add_service_type("Recreation")
        ServiceTypeLibrary.add_service_type("Mortuary")
        ServiceTypeLibrary.add_service_type("Medical Emergency")
        ServiceTypeLibrary.add_service_type("Legal")
        ServiceTypeLibrary.add_service_type("Lodging")
        ServiceTypeLibrary.add_service_type("Home Improvement")


class DefaultPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        name_data_plugin = DefaultNameDataPlugin()
        life_event_plugin = DefaultLifeEventPlugin()

        name_data_plugin.setup(sim, **kwargs)
        life_event_plugin.setup(sim, **kwargs)


def get_plugin() -> Plugin:
    return DefaultPlugin()
