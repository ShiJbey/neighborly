from neighborly.builtin.components import Child, Teen, YoungAdult
from neighborly.core.ecs import Component, GameObject, ISystem, component_info
from neighborly.core.event import Event, EventLog, EventRole
from neighborly.core.time import SimDateTime
from neighborly.plugins.talktown.business_components import School


@component_info("Student", "This entity is a student at the local school")
class Student(Component):
    pass


class GraduatedFromSchoolEvent(Event):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(
            name="GraduatedSchool",
            timestamp=date.to_iso_str(),
            roles=[EventRole("Student", character.id)],
        )


class SchoolSystem(ISystem):
    """Enrolls new students and graduates old students"""

    def process(self, *args, **kwargs) -> None:
        event_logger = self.world.get_resource(EventLog)
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
                    GraduatedFromSchoolEvent(date, self.world.get_gameobject(gid))
                )
