from __future__ import annotations

from typing import List, Literal, Tuple

from neighborly.builtin.components import (
    Age,
    CollegeGraduate,
    CurrentLocation,
    Female,
    Male,
    NonBinary,
)
from neighborly.core.business import Occupation, Unemployed, WorkHistory
from neighborly.core.ecs import GameObject, World
from neighborly.core.query import EcsFindClause, QueryFilterFn
from neighborly.core.relationship import Relationships
from neighborly.core.time import SimDateTime


def friendship_gt(threshold: float) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        results: List[Tuple[int, ...]] = []
        for gid, relationships in world.get_component(Relationships):
            for r in relationships.get_all():
                if r.friendship > threshold:
                    results.append((gid, r.target))
        return results

    return precondition


def friendship_lt(threshold: float) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        results: List[Tuple[int, ...]] = []
        for gid, relationships in world.get_component(Relationships):
            for r in relationships.get_all():
                if r.friendship < threshold:
                    results.append((gid, r.target))
        return results

    return precondition


def romance_gt(threshold: float) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        results: List[Tuple[int, ...]] = []
        for gid, relationships in world.get_component(Relationships):
            for r in relationships.get_all():
                if r.romance > threshold:
                    results.append((gid, r.target))
        return results

    return precondition


def romance_lt(threshold: float) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        results: List[Tuple[int, ...]] = []
        for gid, relationships in world.get_component(Relationships):
            for r in relationships.get_all():
                if r.romance < threshold:
                    results.append((gid, r.target))
        return results

    return precondition


def relationship_has_tags(*tags: str) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        results: List[Tuple[int, ...]] = []
        for gid, relationships in world.get_component(Relationships):
            for r in relationships.get_all_with_tags(*tags):
                results.append((gid, r.target))
        return results

    return precondition


def has_relationship_with_tags(*tags: str) -> QueryFilterFn:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World, *gameobjects: GameObject) -> bool:
        gameobject = gameobjects[0]
        if relationships := gameobject.try_component(Relationships):
            if relationships.get_all_with_tags(*tags):
                return True
        return False

    return precondition


def at_same_location(world: World, *gameobjects: GameObject) -> bool:
    """Return True if these characters are at the same location"""
    a_location = gameobjects[0].get_component(CurrentLocation).location
    b_location = gameobjects[1].get_component(CurrentLocation).location
    return (
        a_location is not None and b_location is not None and a_location == b_location
    )


def over_age(age: int) -> QueryFilterFn:
    def fn(world: World, *gameobjects: GameObject) -> bool:
        age_component = gameobjects[0].try_component(Age)
        if age_component is not None:
            return age_component.value > age

    return fn


def is_single(world: World, *gameobjects: GameObject) -> bool:
    """Return True if this entity has no relationships tagged as significant others"""
    return (
        len(
            gameobjects[0]
            .get_component(Relationships)
            .get_all_with_tags("Significant Other")
        )
        == 0
    )


def is_unemployed(world: World, *gameobjects: GameObject) -> bool:
    """Returns True if this entity does not have a job"""
    return gameobjects[0].has_component(Unemployed)


def is_employed(world: World, *gameobjects: GameObject) -> bool:
    """Returns True if this entity has a job"""
    return gameobjects[0].has_component(Occupation)


def before_year(year: int) -> QueryFilterFn:
    """Return precondition function that checks if the date is before a given year"""

    def fn(world: World, *gameobjects: GameObject) -> bool:
        return world.get_resource(SimDateTime).year < year

    return fn


def after_year(year: int) -> QueryFilterFn:
    """Return precondition function that checks if the date is after a given year"""

    def fn(world: World, *gameobjects: GameObject) -> bool:
        return world.get_resource(SimDateTime).year > year

    return fn


def is_gender(gender: Literal["male", "female", "non-binary"]) -> QueryFilterFn:
    """Return precondition function that checks if an entity is a given gender"""
    gender_component_types = {"male": Male, "female": Female, "non-binary": NonBinary}

    def fn(world: World, *gameobjects: GameObject) -> bool:
        return gameobjects[0].has_component(gender_component_types[gender])

    return fn


def has_any_work_experience(world: World, *gameobjects: GameObject) -> bool:
    """Return True if the entity has any work experience at all"""
    return len(gameobjects[0].get_component(WorkHistory)) > 0


def has_experience_as_a(
    occupation_type: str, years_experience: int = 0
) -> QueryFilterFn:
    """
    Returns Precondition function that returns true if the entity
    has experience as a given occupation type.

    Parameters
    ----------
    occupation_type: str
        The name of the occupation to check for
    years_experience: int
        The number of years of experience the entity needs to have

    Returns
    -------
    QueryFilterFn
        The precondition function used when filling the occupation
    """

    def fn(world: World, *gameobjects: GameObject) -> bool:
        total_experience: int = 0
        gameobject = gameobjects[0]

        work_history = gameobject.try_component(WorkHistory)

        if work_history is None:
            return False

        for entry in work_history.entries[:-1]:
            if entry.occupation_type == occupation_type:
                total_experience += entry.years_held

        if gameobject.has_component(Occupation):
            occupation = gameobject.get_component(Occupation)
            if occupation.occupation_type == occupation_type:
                total_experience += occupation.years_held

        return total_experience >= years_experience

    return fn


def is_college_graduate(world: World, *gameobject: GameObject) -> bool:
    """Return True if the entity is a college graduate"""
    return gameobject[0].has_component(CollegeGraduate)
