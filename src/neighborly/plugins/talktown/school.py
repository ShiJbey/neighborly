import random
from typing import Any, Dict, List

from neighborly.components.character import (
    GameCharacter,
    LifeStage,
    LifeStageType,
)
from neighborly.components.role import (
    IsRole,
    get_roles_with_components,
    add_role,
    remove_role,
)
from neighborly.components.shared import (
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
    Name,
    OwnedBy,
)
from neighborly.core.ecs import (
    Active,
    Component,
    GameObject,
    ISerializable,
    ISystem,
    SystemGroup,
    World,
)
from neighborly.core.life_event import EventRole, LifeEvent
from neighborly.core.settlement import Settlement
from neighborly.core.status import StatusComponent
from neighborly.core.time import SimDateTime
from neighborly.plugins.talktown.business_components import School


class Student(Component, ISerializable):
    """Component attached to a role that identifies the role owner as a student."""

    __slots__ = "school"

    def __init__(self, school: GameObject) -> None:
        super().__init__()
        self.school = school

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(school: {self.school.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {"school": self.school.uid}


class CollegeGraduate(StatusComponent):
    pass


class EnrolledInSchoolEvent(LifeEvent):
    def __init__(
        self, world: World, date: SimDateTime, character: GameObject, school: GameObject
    ) -> None:
        super().__init__(
            world,
            date,
            [EventRole("Character", character), EventRole("School", school)],
        )


class GraduatedFromSchoolEvent(LifeEvent):
    def __init__(
        self, world: World, date: SimDateTime, character: GameObject, school: GameObject
    ) -> None:
        super().__init__(
            world,
            date,
            [EventRole("Character", character), EventRole("School", school)],
        )


class EnrollInSchoolSystem(ISystem):
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

        for guid, (_, _, life_stage, current_settlement) in world.get_components(
            (GameCharacter, Active, LifeStage, CurrentSettlement)
        ):
            # Reject anyone older than teenage
            if life_stage.life_stage > LifeStageType.Adolescent:
                continue

            # Reject people who are already students
            if (
                len(
                    get_roles_with_components(
                        world.gameobject_manager.get_gameobject(guid), Student
                    )
                )
                > 0
            ):
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

                student_role = world.gameobject_manager.spawn_gameobject(
                    components=[
                        Name("Student"),
                        IsRole(),
                        Student(chosen_school),
                        OwnedBy(new_student),
                    ],
                    name=f"Student @ {chosen_school.get_component(Name).value}",
                )

                chosen_school.get_component(School).add_student(student_role)

                add_role(new_student, student_role)

                new_student.get_component(FrequentedLocations).add(chosen_school)
                chosen_school.get_component(FrequentedBy).add(new_student)

                event = EnrolledInSchoolEvent(
                    world, current_date, new_student, chosen_school
                )

                event.dispatch()


class GraduateAdultStudentsSystem(ISystem):
    """Graduates all the enrolled students who are now adults."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, (school,) in world.get_components((School,)):
            school_obj = world.gameobject_manager.get_gameobject(guid)
            for student_role in school.students:
                student = student_role.get_component(OwnedBy).owner

                if (
                    student.get_component(LifeStage).life_stage
                    >= LifeStageType.YoungAdult
                ):
                    school.remove_student(student_role)
                    remove_role(student, student_role)
                    student_role.destroy()

                    student.get_component(FrequentedLocations).remove(school_obj)
                    school_obj.get_component(FrequentedBy).remove(student)

                    event = GraduatedFromSchoolEvent(
                        world, current_date, student, school_obj
                    )
                    world.event_manager.dispatch_event(event)


class SchoolSystemGroup(SystemGroup):
    """Groups systems related to characters going to school."""

    pass
