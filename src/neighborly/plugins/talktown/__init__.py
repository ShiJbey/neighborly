import logging
import os
import pathlib

from ordered_set import OrderedSet

from neighborly.builtin.statuses import Child, Teen, YoungAdult
from neighborly.core.ecs import GameObject, World, ISystem
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEventLog, LifeEvent, EventRole
from neighborly.core.rng import DefaultRNG
from neighborly.core.status import Status
from neighborly.core.time import SimDateTime
from neighborly.core.town import Town
from neighborly.simulation import Plugin, Simulation

logger = logging.getLogger(__name__)

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent


class School:
    """A school is where Characters that are Children through Teen study"""

    __slots__ = "students"

    def __init__(self) -> None:
        super().__init__()
        self.students: OrderedSet[int] = OrderedSet()

    def add_student(self, student: int) -> None:
        """Add student to the school"""
        self.students.add(student)

    def remove_student(self, student: int) -> None:
        """Remove student from the school"""
        self.students.add(student)


class Student(Status):

    def __init__(self):
        super().__init__("Student", "This character is a student at the local school")


class SchoolSystem(ISystem):
    """Enrolls new students and graduates old students"""

    def process(self, *args, **kwargs) -> None:
        try:
            school = self.world.get_resource(School)
        except KeyError:
            return

        event_logger = self.world.get_resource(LifeEventLog)
        date = self.world.get_resource(SimDateTime)

        # Enroll children
        for gid, child in self.world.get_component(Child):
            if not child.gameobject.has_component(Student):
                school.add_student(gid)
                child.gameobject.add_component(Student())

        # Enroll teens
        for gid, teen in self.world.get_component(Teen):
            if not teen.gameobject.has_component(Student):
                school.add_student(gid)
                teen.gameobject.add_component(Student())

        # Graduate young adults
        for gid, (young_adult, _) in self.world.get_components(YoungAdult, Student):
            school.remove_student(gid)
            young_adult.gameobject.remove_component(Student)
            event_logger.record_event(
                LifeEvent(
                    "GraduatedSchool",
                    date.to_iso_str(),
                    [EventRole("Student", gid)]
                )
            )


def establish_town(world: World, **kwargs) -> None:
    """
    Adds an initial set of families and businesses
    to the start of the town.

    This system runs once, then removes itself from
    the ECS to free resources.

    Parameters
    ----------
    world : World
        The world instance of the simulation

    Notes
    -----
    This function is based on the original Simulation.establish_setting
    method in talktown.
    """
    logger.debug("Establishing town")

    engine = world.get_resource(NeighborlyEngine)

    town = GameObject(components=[Town()])

    vacant_lots = town.get_component(Town).layout.get_vacancies()
    # Each family requires 2 lots (1 for a house, 1 for a business)
    # Save two lots for either a coalmine, quarry, or farm
    n_families_to_add = (len(vacant_lots) // 2) - 1

    for _ in range(n_families_to_add - 1):
        # create residents
        # create Farm
        farm = engine.spawn_business(world, "Farm")
        # trigger hiring event
        # trigger home move event

    random_num = world.get_resource(DefaultRNG).random()
    if random_num < 0.2:
        # Create a Coalmine 20% of the time
        coalmine = engine.spawn_business("Coal Mine")
    elif 0.2 <= random_num < 0.35:
        # Create a Quarry 15% of the time
        quarry = engine.spawn_business("Quarry")
    else:
        # Create Farm 65% of the time
        farm = engine.spawn_business("Farm")

    logger.debug("Town established. 'establish_town' function removed from systems")


class TalkOfTheTownPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        sim.add_system(SchoolSystem())


def get_plugin() -> Plugin:
    return TalkOfTheTownPlugin()
