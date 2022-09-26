from ordered_set import OrderedSet

from neighborly.builtin.statuses import Child, Teen, YoungAdult
from neighborly.core.ecs import Component, ISystem
from neighborly.core.life_event import LifeEvent, LifeEventLog, Role
from neighborly.core.status import Status
from neighborly.core.time import SimDateTime


class School(Component):
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
        event_logger = self.world.get_resource(LifeEventLog)
        date = self.world.get_resource(SimDateTime)

        for _, school in self.world.get_component(School):
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
                        [Role("Student", gid)],
                    )
                )
