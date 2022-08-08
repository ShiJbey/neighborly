import logging
import os
from pathlib import Path

from neighborly.builtin.events import (
    become_enemies_event,
    become_friends_event,
    dating_break_up_event,
    depart_due_to_unemployment,
    divorce_event,
    hire_employee_event,
    hiring_business_role,
    marriage_event,
    potential_spouse_role,
    pregnancy_event,
    retire_event,
    single_person_role_type,
    start_dating_event,
    unemployed_role,
)
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import EventRoles, LifeEvents
from neighborly.simulation import Plugin, Simulation

logger = logging.getLogger(__name__)

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


class DefaultNameDataPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        self.initialize_tracery_name_factory(sim.get_engine())

    def initialize_tracery_name_factory(self, engine: NeighborlyEngine) -> None:
        # Load character name data
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
        EventRoles.register(
            name="PotentialSpouse", event_role_type=potential_spouse_role()
        )
        EventRoles.register("SinglePerson", single_person_role_type())
        EventRoles.register("HiringBusiness", hiring_business_role())
        EventRoles.register("Unemployed", unemployed_role())
        LifeEvents.register(hire_employee_event())
        LifeEvents.register(marriage_event())
        LifeEvents.register(become_friends_event())
        LifeEvents.register(become_enemies_event())
        LifeEvents.register(start_dating_event())
        LifeEvents.register(dating_break_up_event())
        LifeEvents.register(divorce_event())
        LifeEvents.register(marriage_event())
        LifeEvents.register(pregnancy_event())
        LifeEvents.register(depart_due_to_unemployment())
        LifeEvents.register(retire_event())
