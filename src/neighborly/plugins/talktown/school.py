from typing import Any, List

from neighborly.components.character import (
    Adolescent,
    Adult,
    Child,
    GameCharacter,
    YoungAdult,
)
from neighborly.components.shared import Active
from neighborly.core.ecs import GameObject, ISystem
from neighborly.core.ecs.ecs import World
from neighborly.core.life_event import LifeEvent, LifeEventBuffer
from neighborly.core.roles import Role
from neighborly.core.status import StatusComponent
from neighborly.core.time import SimDateTime
from neighborly.plugins.talktown.business_components import School
from neighborly.utils.statuses import add_status, remove_status


class Student(StatusComponent):
    pass


class CollegeGraduate(StatusComponent):
    pass


class EnrolledInSchoolEvent(LifeEvent):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(
            date,
            [Role("Character", character)],
        )


class GraduatedFromSchoolEvent(LifeEvent):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(
            date,
            [Role("Character", character)],
        )


class SchoolSystem(ISystem):
    """Enrolls new students and graduates old students"""

    @staticmethod
    def get_unenrolled_students(world: World) -> List[GameObject]:
        candidates = [
            world.get_gameobject(res[0])
            for res in world.get_components((GameCharacter, Active, Child))
        ]

        candidates.extend(
            [
                world.get_gameobject(res[0])
                for res in world.get_components((GameCharacter, Active, Adolescent))
            ]
        )

        candidates = [c for c in candidates if not c.has_component(Student)]

        return candidates

    @staticmethod
    def get_adult_students(world: World) -> List[GameObject]:
        candidates = [
            world.get_gameobject(res[0])
            for res in world.get_components((GameCharacter, Active, Student, Adult))
        ]

        candidates.extend(
            [
                world.get_gameobject(res[0])
                for res in world.get_components((GameCharacter, Active, YoungAdult))
            ]
        )

        return candidates

    def process(self, *args: Any, **kwargs: Any) -> None:
        life_event_buffer = self.world.get_resource(LifeEventBuffer)
        date = self.world.get_resource(SimDateTime)

        for _, school in self.world.get_component(School):
            for character in self.get_unenrolled_students(self.world):
                school.add_student(character.uid)
                add_status(character, Student())
                life_event_buffer.append(EnrolledInSchoolEvent(date, character))

            # Graduate young adults
            for character in self.get_adult_students(self.world):
                school.remove_student(character.uid)
                remove_status(character, Student)
                life_event_buffer.append(GraduatedFromSchoolEvent(date, character))
