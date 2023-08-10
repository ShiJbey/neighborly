import random
from typing import Any, Dict, List

from neighborly.components.character import GameCharacter, LifeStage, LifeStageType
from neighborly.components.shared import FrequentedLocations
from neighborly.ecs import Active, GameObject, System, SystemGroup, World
from neighborly.life_event import EventHistory, EventLog, LifeEvent
from neighborly.plugins.talktown.businesses import School
from neighborly.roles import IRole, Roles
from neighborly.statuses import IStatus
from neighborly.time import SimDateTime


class Student(IRole):
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

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        self.character.get_component(EventHistory).append(self)

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

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)

        self.character.get_component(EventHistory).append(self)

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


class EnrollInSchoolSystem(System):
    """Enrolls children and adolescents as new students in schools."""

    @staticmethod
    def get_schools(world: World) -> List[GameObject]:
        """Find all schools within a settlement.

        Parameters
        ----------
        world
            The World instance.

        Returns
        -------
        List[GameObject]
            A list of all schools in the settlement.
        """
        schools: List[GameObject] = [
            world.gameobject_manager.get_gameobject(guid)
            for guid, _ in world.get_components((Active, School))
        ]

        return schools

    def on_update(self, world: World) -> None:
        # Cache the lists of schools per settlement to reduce lookups
        schools = EnrollInSchoolSystem.get_schools(world)

        # Return early if no schools are available
        if len(schools) == 0:
            return

        rng = world.resource_manager.get_resource(random.Random)

        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, (_, _, life_stage, roles) in world.get_components(
            (GameCharacter, Active, LifeStage, Roles)
        ):
            # Reject anyone older than teenage
            if life_stage.life_stage > LifeStageType.Adolescent:
                continue

            # Reject people who are already students
            if len(roles.get_roles_of_type(Student)) > 0:
                continue

            # Choose a school in the settlement to enroll into
            chosen_school = rng.choice(schools)

            new_student = world.gameobject_manager.get_gameobject(guid)

            chosen_school.get_component(School).add_student(new_student)

            new_student.add_component(Student, school=chosen_school)

            new_student.get_component(FrequentedLocations).add_location(chosen_school)

            EnrolledInSchoolEvent(
                world, current_date, new_student, chosen_school
            ).dispatch()


class GraduateAdultStudentsSystem(System):
    """Graduates all the enrolled students who are now adults."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, (student, life_stage) in world.get_components((Student, LifeStage)):
            character = world.gameobject_manager.get_gameobject(guid)
            if life_stage.life_stage >= LifeStageType.YoungAdult:
                school_component = student.school.get_component(School)

                school_component.remove_student(character)
                character.remove_component(type(student))
                character.get_component(FrequentedLocations).remove_location(
                    student.school
                )

                GraduatedFromSchoolEvent(
                    world, current_date, character, student.school
                ).dispatch()


class SchoolSystemGroup(SystemGroup):
    """Groups systems related to characters going to school."""

    pass
