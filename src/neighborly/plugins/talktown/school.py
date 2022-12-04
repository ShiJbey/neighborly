from typing import Any, ClassVar

from neighborly.builtin.components import Active
from neighborly.builtin.role_filters import life_stage_ge, life_stage_le
from neighborly.core.character import GameCharacter, LifeStage, LifeStageValue
from neighborly.core.ecs import Component, GameObject, ISystem, component_info
from neighborly.core.event import Event, EventLog, EventRole
from neighborly.core.query import Query, QueryBuilder, and_
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

    unenrolled_student_query: ClassVar[Query] = (
        QueryBuilder()
        .with_((GameCharacter, Active, LifeStage))
        .filter_(
            and_(
                life_stage_le(LifeStageValue.Adolescent),
                lambda world, *gameobjects: not gameobjects[0].has_component(Student),
            )
        )
        .build()
    )

    adult_student_query: ClassVar[Query] = (
        QueryBuilder()
        .with_((GameCharacter, Active, LifeStage, Student))
        .filter_(life_stage_ge(LifeStageValue.YoungAdult))
        .build()
    )

    def process(self, *args: Any, **kwargs: Any) -> None:
        event_logger = self.world.get_resource(EventLog)
        date = self.world.get_resource(SimDateTime)

        for _, school in self.world.get_component(School):
            for res in self.unenrolled_student_query.execute(self.world):
                gid = res[0]
                school.add_student(gid)
                self.world.get_gameobject(gid).add_component(Student())

            # Graduate young adults
            for res in self.adult_student_query.execute(self.world):
                gid = res[0]
                school.remove_student(gid)
                student = self.world.get_gameobject(gid)
                student.remove_component(Student)
                event_logger.record_event(GraduatedFromSchoolEvent(date, student))
