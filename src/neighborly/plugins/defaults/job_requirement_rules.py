"""Default job requirement rules

This module contains definitions for job requirement rule functions
used to precondition when characters are allowed to hold a certain
occupation.

"""

from typing import Any

from neighborly.components.business import (
    JobRequirementLibrary,
    Occupation,
    OccupationLibrary,
    WorkHistory,
)
from neighborly.components.character import Gender, GenderType, RoleTracker
from neighborly.components.shared import Age
from neighborly.core.ecs import GameObject
from neighborly.core.time import DAYS_PER_YEAR, SimDateTime
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="default job requirements plugin",
    plugin_id="default.job_requirements",
    version="0.1.0",
)


def has_component(gameobject: GameObject, *args: Any) -> bool:
    component_name: str
    (component_name,) = args
    return gameobject.has_component(
        gameobject.world.get_component_info(component_name).component_type
    )


def has_gender(gameobject: GameObject, *args: Any) -> bool:
    gender_name: str
    (gender_name,) = args
    if gender := gameobject.try_component(Gender):
        return gender.gender == GenderType[gender_name]
    return False


def over_age(gameobject: GameObject, *args: Any) -> bool:
    years: float
    (years,) = args
    if age := gameobject.try_component(Age):
        return age.value > years
    return False


def has_work_experience_as(gameobject: GameObject, *args: Any) -> bool:
    """
    Returns Precondition function that returns true if the entity
    has experience as a given occupation type.

    Parameters
    ----------
    occupation_type
        The name of the occupation to check for
    years_experience
        The number of years of experience the entity needs to have
    """

    occupation_type_name: str
    years_experience: int
    (occupation_type_name, years_experience) = args

    occupation_type = gameobject.world.get_resource(OccupationLibrary).get(
        occupation_type_name
    )

    total_experience: float = 0

    current_date = gameobject.world.get_resource(SimDateTime)

    work_history = gameobject.try_component(WorkHistory)

    if work_history is None:
        return False

    # Add up an experience from their past work history
    for entry in work_history.entries[:-1]:
        if entry.occupation_type == occupation_type:
            total_experience += entry.years_held

    # Add any experience from their current occupations
    role_tracker = gameobject.get_component(RoleTracker)

    # This technically double-counts time for characters that may have multiple
    # occupations of the same type
    for role in role_tracker.roles:
        if occupation := role.try_component(Occupation):
            if occupation.occupation_type == occupation_type:
                total_experience += (
                    float((current_date - occupation.start_date).total_days)
                    / DAYS_PER_YEAR
                )

    return total_experience >= years_experience


def has_any_work_experience(gameobject: GameObject, *args: Any) -> bool:
    """
    Returns Precondition function that returns true if the entity
    has experience as a given occupation type.

    Parameters
    ----------
    years_experience
        The number of years of experience the entity needs to have
    """

    years_experience: int
    (years_experience,) = args

    total_experience: float = 0

    current_date = gameobject.world.get_resource(SimDateTime)

    work_history = gameobject.try_component(WorkHistory)

    if work_history is None:
        return False

    for entry in work_history.entries:
        total_experience += entry.years_held

        if total_experience >= years_experience:
            return True

    # Add any experience from their current occupations
    role_tracker = gameobject.get_component(RoleTracker)

    # This technically double-counts time for characters that may have multiple
    # occupations of the same type
    for role in role_tracker.roles:
        if occupation := role.try_component(Occupation):
            total_experience += (
                float((current_date - occupation.start_date).total_days) / DAYS_PER_YEAR
            )

    if gameobject.has_component(Occupation):
        occupation = gameobject.get_component(Occupation)
        total_experience += (
            float((current_date - occupation.start_date).total_days) / DAYS_PER_YEAR
        )

    return total_experience >= years_experience


def setup(sim: Neighborly, **kwargs: Any):
    job_requirement_library = sim.world.get_resource(JobRequirementLibrary)
    job_requirement_library.add("has_component", has_component)
    job_requirement_library.add("has_gender", has_gender)
    job_requirement_library.add("over_age", over_age)
    job_requirement_library.add("has_work_experience_as", has_work_experience_as)
    job_requirement_library.add("has_any_work_experience", has_any_work_experience)
