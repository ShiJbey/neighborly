import os
from pathlib import Path
from typing import Optional, Tuple

from neighborly.builtin.components import Age
from neighborly.builtin.events import (
    depart_due_to_unemployment,
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
from neighborly.builtin.systems import (
    BuildBusinessSystem,
    BuildHousingSystem,
    BusinessUpdateSystem,
    CharacterAgingSystem,
    ClosedForBusinessSystem,
    FindBusinessOwnerSystem,
    FindEmployeesSystem,
    OpenForBusinessSystem,
    PendingOpeningSystem,
    PregnancySystem,
    RoutineSystem,
    SpawnResidentSystem,
)
from neighborly.core.business import Occupation
from neighborly.core.constants import (
    BUSINESS_UPDATE_PHASE,
    CHARACTER_UPDATE_PHASE,
    TOWN_SYSTEMS_PHASE,
)
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvents, LifeEventSystem
from neighborly.core.personal_values import PersonalValues
from neighborly.core.time import TimeDelta
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
        LifeEvents.add(marriage_event())
        # LifeEvents.add(become_friends_event())
        # LifeEvents.add(become_enemies_event())
        LifeEvents.add(depart_due_to_unemployment())
        LifeEvents.add(start_dating_event())
        LifeEvents.add(stop_dating_event())
        LifeEvents.add(divorce_event())
        LifeEvents.add(pregnancy_event())
        LifeEvents.add(retire_event())
        LifeEvents.add(find_own_place_event())
        LifeEvents.add(die_of_old_age())
        LifeEvents.add(go_out_of_business_event())


def get_values_compatibility(
    world: World, subject_id: int, target_id: int
) -> Optional[Tuple[int, int]]:
    """Return value [-1.0, 1.0] representing the compatibility of two characters"""
    subject_values = world.get_gameobject(subject_id).try_component(PersonalValues)
    target_values = world.get_gameobject(target_id).try_component(PersonalValues)

    if subject_values is not None and target_values is not None:
        compatibility = PersonalValues.compatibility(subject_values, target_values) * 5
        return int(compatibility), int(compatibility)


def job_level_difference_debuff(
    world: World, subject_id: int, target_id: int
) -> Optional[Tuple[int, int]]:
    """
    This makes people with job-level differences less likely to develop romantic feelings
    for one another (missing source)
    """
    subject_job = world.get_gameobject(subject_id).try_component(Occupation)
    target_job = world.get_gameobject(target_id).try_component(Occupation)

    if subject_job is not None and target_job is None:
        return 0, -1

    if subject_job is None and target_job is not None:
        return 0, 1

    if subject_job is not None and target_job is not None:
        character_a_level = subject_job.level if subject_job else 0
        character_b_level = target_job.level if target_job else 0
        compatibility = int(5 - (abs(character_a_level - character_b_level)))
        return compatibility, compatibility


def age_difference_debuff(
    world: World, subject_id: int, target_id: int
) -> Optional[Tuple[int, int]]:
    """How does age difference affect developing romantic feelings
    People with larger age gaps are less likely to develop romantic feelings
    (missing source)
    """
    character_a_age = world.get_gameobject(subject_id).get_component(Age).value
    character_b_age = world.get_gameobject(target_id).get_component(Age).value

    friendship_buff = int(12 / (character_b_age - character_a_age))
    romance_buff = int(8 / (character_b_age - character_a_age))

    return friendship_buff, romance_buff


class DefaultPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        name_data_plugin = DefaultNameDataPlugin()
        life_event_plugin = DefaultLifeEventPlugin()

        name_data_plugin.setup(sim, **kwargs)
        life_event_plugin.setup(sim, **kwargs)

        # SocializeSystem.add_compatibility_check(get_values_compatibility)
        # SocializeSystem.add_compatibility_check(job_level_difference_debuff)
        # SocializeSystem.add_compatibility_check(age_difference_debuff)

        sim.world.add_system(CharacterAgingSystem(), priority=CHARACTER_UPDATE_PHASE)
        sim.world.add_system(RoutineSystem(), priority=CHARACTER_UPDATE_PHASE)
        sim.world.add_system(BusinessUpdateSystem(), priority=BUSINESS_UPDATE_PHASE)
        sim.world.add_system(FindBusinessOwnerSystem(), priority=BUSINESS_UPDATE_PHASE)
        sim.world.add_system(FindEmployeesSystem(), priority=BUSINESS_UPDATE_PHASE)
        # self.add_system(
        #     UnemploymentSystem(days_to_departure=30), priority=CHARACTER_UPDATE_PHASE
        # )
        # self.add_system(SocializeSystem(), priority=CHARACTER_ACTION_PHASE)
        sim.world.add_system(PregnancySystem(), priority=CHARACTER_UPDATE_PHASE)
        sim.world.add_system(
            PendingOpeningSystem(days_before_demolishing=9999),
            priority=BUSINESS_UPDATE_PHASE,
        )
        sim.world.add_system(OpenForBusinessSystem(), priority=BUSINESS_UPDATE_PHASE)
        sim.world.add_system(ClosedForBusinessSystem(), priority=BUSINESS_UPDATE_PHASE)
        sim.world.add_system(
            LifeEventSystem(interval=TimeDelta(months=2)), priority=TOWN_SYSTEMS_PHASE
        )

        sim.world.add_system(
            BuildHousingSystem(chance_of_build=1.0), priority=TOWN_SYSTEMS_PHASE
        )
        sim.world.add_system(
            SpawnResidentSystem(interval=TimeDelta(days=7), chance_spawn=1.0),
            priority=TOWN_SYSTEMS_PHASE,
        )
        sim.world.add_system(
            BuildBusinessSystem(interval=TimeDelta(days=5)), priority=TOWN_SYSTEMS_PHASE
        )


def get_plugin() -> Plugin:
    return DefaultPlugin()
