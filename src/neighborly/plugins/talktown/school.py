import random
from typing import Any, Dict, Iterable, List

from neighborly.components.character import GameCharacter, LifeStage, LifeStageType
from neighborly.components.role import Roles, add_role, remove_role
from neighborly.components.shared import CurrentSettlement
from neighborly.core.ecs import (
    Active,
    Component,
    GameObject,
    ISerializable,
    SystemBase,
    SystemGroup,
    World,
)
from neighborly.core.life_event import LifeEvent
from neighborly.core.settlement import Settlement
from neighborly.core.status import IStatus
from neighborly.core.time import SimDateTime
from neighborly.plugins.talktown.business_components import School
from neighborly.utils.common import add_frequented_location, remove_frequented_location


class Student(Component, ISerializable):
    """Component attached to a role that identifies the role owner as a student."""

    __slots__ = "school"

    school: GameObject
    """The school the student is enrolled at."""

    def __init__(self, school: GameObject) -> None:
        super().__init__()
        self.school = school

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(school: {self.school.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {"school": self.school.uid}


class CollegeGraduate(IStatus):
    pass


class EnrolledInSchoolEvent(LifeEvent):
    """Event dispatched when a child/adolescent enrolls at a school."""

    __slots__ = "character", "school"

    character: GameObject
    """The character that enrolled."""

    school: GameObject
    """The school they enrolled at."""

    def __init__(
        self, world: World, date: SimDateTime, character: GameObject, school: GameObject
    ) -> None:
        super().__init__(world, date)
        self.character = character
        self.school = school

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.year,
            "character": self.character.uid,
            "school": self.school.uid,
        }

    def __str__(self) -> str:
        return "{} [@ {}] {} enrolled in school at '{}'.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
            self.school.name,
        )


class GraduatedFromSchoolEvent(LifeEvent):
    """Event dispatched when a character graduates from school."""

    __slots__ = "character", "school"

    character: GameObject
    """The graduate."""

    school: GameObject
    """The school they graduated from."""

    def __init__(
        self, world: World, date: SimDateTime, character: GameObject, school: GameObject
    ) -> None:
        super().__init__(world, date)
        self.character = character
        self.school = school

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.year,
            "character": self.character.uid,
            "school": self.school.uid,
        }

    def __str__(self) -> str:
        return "{} [@ {}] {} graduated from school at '{}'.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
            self.school.name,
        )


class EnrollInSchoolSystem(SystemBase):
    """Enrolls children and adolescents as new students in schools."""

    @staticmethod
    def get_schools_in_settlement(settlement: GameObject) -> List[GameObject]:
        """Find all schools within a settlement.

        Parameters
        ----------
        settlement
            The settlement to check.

        Returns
        -------
        List[GameObject]
            A list of all schools in the settlement.
        """
        settlement_comp = settlement.get_component(Settlement)

        schools: List[GameObject] = []

        for entry in settlement_comp.businesses:
            if entry.has_components(Active, School):
                schools.append(entry)

        return schools

    def on_update(self, world: World) -> None:
        # Cache the lists of schools per settlement to reduce lookups
        school_list_cache: Dict[GameObject, List[GameObject]] = {}

        rng = world.resource_manager.get_resource(random.Random)

        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, (_, _, life_stage, current_settlement, roles) in world.get_components(
            (GameCharacter, Active, LifeStage, CurrentSettlement, Roles)
        ):
            # Reject anyone older than teenage
            if life_stage.life_stage > LifeStageType.Adolescent:
                continue

            # Reject people who are already students
            if len(roles.get_roles_of_type(Student)) > 0:
                continue

            # Choose a school in the settlement to enroll into
            if current_settlement.settlement in school_list_cache:
                school_choices = school_list_cache[current_settlement.settlement]
            else:
                school_choices = EnrollInSchoolSystem.get_schools_in_settlement(
                    current_settlement.settlement
                )
                school_list_cache[current_settlement.settlement] = school_choices

            if school_choices:
                chosen_school = rng.choice(school_choices)
                new_student = world.gameobject_manager.get_gameobject(guid)

                student = world.gameobject_manager.create_component(
                    Student, school=chosen_school
                )

                chosen_school.get_component(School).add_student(new_student)

                add_role(new_student, student)

                add_frequented_location(new_student, chosen_school)

                event = EnrolledInSchoolEvent(
                    world, current_date, new_student, chosen_school
                )

                event.dispatch()


class GraduateAdultStudentsSystem(SystemBase):
    """Graduates all the enrolled students who are now adults."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, (student, life_stage) in world.get_components((Student, LifeStage)):
            character = world.gameobject_manager.get_gameobject(guid)
            if life_stage.life_stage >= LifeStageType.YoungAdult:
                school_component = student.school.get_component(School)

                school_component.remove_student(character)
                remove_role(character, type(student))

                remove_frequented_location(character, student.school)

                event = GraduatedFromSchoolEvent(
                    world, current_date, character, student.school
                )
                world.event_manager.dispatch_event(event)


class SchoolSystemGroup(SystemGroup):
    """Groups systems related to characters going to school."""

    pass
