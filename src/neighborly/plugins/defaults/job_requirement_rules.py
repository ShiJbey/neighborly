"""Default job requirement rules

This module contains definitions for job requirement rule functions
used to precondition when characters are allowed to hold a certain
occupation.

"""

from typing import Any

from neighborly.components.business import Occupation, WorkHistory
from neighborly.components.character import Gender
from neighborly.components.shared import Age
from neighborly.ecs import GameObject
from neighborly.roles import Roles
from neighborly.time import SimDateTime


def has_component(gameobject: GameObject, *args: Any) -> bool:
    component_name: str
    (component_name,) = args
    return gameobject.has_component(
        gameobject.world.gameobject_manager.get_component_info(
            component_name
        ).component_type
    )


def has_gender(gameobject: GameObject, *args: Any) -> bool:
    gender_name: str
    (gender_name,) = args
    if gender := gameobject.try_component(Gender):
        return type(gender.gender_type).__name__ == gender_name
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
    gameobject
        The gameobject to check
    """

    occupation_type_name: str
    years_experience: int
    (occupation_type_name, years_experience) = args

    occupation_type = gameobject.world.gameobject_manager.get_component_info(
        occupation_type_name
    ).component_type

    total_experience: float = 0

    current_date = gameobject.world.resource_manager.get_resource(SimDateTime)

    work_history = gameobject.try_component(WorkHistory)

    if work_history is None:
        return False

    # Add up an experience from their past work history
    for entry in work_history.entries[:-1]:
        if entry.occupation_type == occupation_type:
            total_experience += entry.years_held

    # This technically double-counts time for characters that may have multiple
    # occupations of the same type
    for occupation in gameobject.get_component(Roles).get_roles_of_type(Occupation):
        if isinstance(occupation, occupation_type):
            total_experience += current_date.year - occupation.start_year

    return total_experience >= years_experience


def has_any_work_experience(gameobject: GameObject, *args: Any) -> bool:
    """
    Returns Precondition function that returns true if the entity
    has experience as a given occupation type.

    Parameters
    ----------
    gameobject
        The gameobject to check
    """

    years_experience: int
    (years_experience,) = args

    total_experience: float = 0

    current_date = gameobject.world.resource_manager.get_resource(SimDateTime)

    work_history = gameobject.try_component(WorkHistory)

    if work_history is None:
        return False

    for entry in work_history.entries:
        total_experience += entry.years_held

        if total_experience >= years_experience:
            return True

    # Add any experience from their current occupations
    for occupation in gameobject.get_component(Roles).get_roles_of_type(Occupation):
        total_experience = current_date.year - occupation.start_year

    return total_experience >= years_experience
