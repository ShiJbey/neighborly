import os
from pathlib import Path
from typing import Any

from neighborly.constants import (
    BUSINESS_UPDATE_PHASE,
    CHARACTER_UPDATE_PHASE,
    TOWN_SYSTEMS_PHASE,
)
from neighborly.core.event import EventLog
from neighborly.core.time import TimeDelta
from neighborly.engine import LifeEvents, NeighborlyEngine
from neighborly.plugins.defaults import event_callbacks
from neighborly.plugins.defaults.life_events import (
    die_of_old_age,
    divorce_event,
    find_own_place_event,
    go_out_of_business_event,
    marriage_event,
    pregnancy_event,
    retire_event,
    start_dating_event,
    stop_dating_event,
)
from neighborly.simulation import Plugin, Simulation
from neighborly.systems import (
    BuildBusinessSystem,
    BuildHousingSystem,
    BusinessUpdateSystem,
    CharacterAgingSystem,
    FindEmployeesSystem,
    SpawnResidentSystem,
)

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


class DefaultNameDataPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs: Any) -> None:
        self.initialize_tracery_name_factory(sim.engine)

    @staticmethod
    def initialize_tracery_name_factory(engine: NeighborlyEngine) -> None:
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
    def setup(self, sim: Simulation, **kwargs: Any) -> None:
        LifeEvents.add(marriage_event())
        # LifeEvents.add(become_friends_event())
        # LifeEvents.add(become_enemies_event())
        LifeEvents.add(start_dating_event())
        LifeEvents.add(stop_dating_event())
        LifeEvents.add(divorce_event())
        LifeEvents.add(pregnancy_event())
        LifeEvents.add(retire_event())
        LifeEvents.add(find_own_place_event())
        LifeEvents.add(die_of_old_age())
        LifeEvents.add(go_out_of_business_event())


class DefaultPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs: Any) -> None:

        resident_spawn_interval_days: int = kwargs.get(
            "resident_spawn_interval_days", 7
        )
        business_spawn_interval_days: int = kwargs.get(
            "business_spawn_interval_days", 5
        )
        activate_name_data_plugin: bool = kwargs.get("activate_name_data_plugin", True)
        activate_life_event_plugin: bool = kwargs.get(
            "activate_life_event_plugin", True
        )

        if activate_name_data_plugin:
            name_data_plugin = DefaultNameDataPlugin()
            name_data_plugin.setup(sim, **kwargs)

        if activate_life_event_plugin:
            life_event_plugin = DefaultLifeEventPlugin()
            life_event_plugin.setup(sim, **kwargs)

        sim.world.add_system(CharacterAgingSystem(), priority=CHARACTER_UPDATE_PHASE)
        sim.world.add_system(BusinessUpdateSystem(), priority=BUSINESS_UPDATE_PHASE)
        sim.world.add_system(FindEmployeesSystem(), priority=BUSINESS_UPDATE_PHASE)
        sim.world.add_system(BuildHousingSystem(), priority=TOWN_SYSTEMS_PHASE)
        sim.world.add_system(
            SpawnResidentSystem(interval=TimeDelta(days=resident_spawn_interval_days)),
            priority=TOWN_SYSTEMS_PHASE,
        )
        sim.world.add_system(
            BuildBusinessSystem(interval=TimeDelta(days=business_spawn_interval_days)),
            priority=TOWN_SYSTEMS_PHASE,
        )

        sim.world.get_resource(EventLog).on(
            "Depart", event_callbacks.on_depart_callback
        )

        sim.world.get_resource(EventLog).on(
            "Retire", event_callbacks.remove_retired_from_occupation
        )

        sim.world.get_resource(EventLog).on(
            "Retire", event_callbacks.remove_retired_from_occupation
        )

        sim.world.get_resource(EventLog).on(
            "Death", event_callbacks.remove_deceased_from_occupation
        )

        sim.world.get_resource(EventLog).on(
            "Death", event_callbacks.remove_deceased_from_residence
        )

        sim.world.get_resource(EventLog).on(
            "Depart", event_callbacks.remove_departed_from_residence
        )

        sim.world.get_resource(EventLog).on(
            "Depart", event_callbacks.remove_departed_from_occupation
        )


def get_plugin() -> Plugin:
    return DefaultPlugin()
