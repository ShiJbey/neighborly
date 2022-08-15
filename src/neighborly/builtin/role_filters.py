from __future__ import annotations

from typing import Any, Literal, Type

from neighborly.builtin.statuses import (
    CollegeGraduate,
    Dating,
    Female,
    InTheWorkforce,
    Male,
    Married,
    NonBinary,
    Retired,
)
from neighborly.core.business import Occupation, WorkHistory
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.life_event import RoleFilterFn
from neighborly.core.relationship import RelationshipGraph, RelationshipTag
from neighborly.core.time import SimDateTime


def over_age(age: int) -> RoleFilterFn:
    def fn(world: World, gameobject: GameObject, **kwargs) -> bool:
        return gameobject.get_component(GameCharacter).age > age

    return fn


def is_man(world: World, gameobject: GameObject, **kwargs) -> bool:
    """Return true if GameObject is a man"""
    return gameobject.has_component(Male)


def older_than(age: int):
    def precondition_fn(world: World, gameobject: GameObject, **kwargs) -> bool:
        return gameobject.get_component(GameCharacter).age > age

    return precondition_fn


def is_single(world: World, gameobject: GameObject, **kwargs) -> bool:
    """Return True if this character has no relationships tagged as significant others"""
    rel_graph = world.get_resource(RelationshipGraph)
    significant_other_relationships = rel_graph.get_all_relationships_with_tags(
        gameobject.id, RelationshipTag.SignificantOther
    )
    return (
        bool(significant_other_relationships)
        and not gameobject.has_component(Married)
        and not gameobject.has_component(Dating)
    )


def is_unemployed(world: World, gameobject: GameObject, **kwargs) -> bool:
    """Returns True if this character does not have a job"""
    return (
        not gameobject.has_component(Occupation)
        and gameobject.has_component(InTheWorkforce)
        and not gameobject.has_component(Retired)
    )


def is_employed(world: World, gameobject: GameObject, **kwargs) -> bool:
    """Returns True if this character has a job"""
    return gameobject.has_component(Occupation)


def before_year(year: int) -> RoleFilterFn:
    """Return precondition function that checks if the date is before a given year"""

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return world.get_resource(SimDateTime).year < year

    return fn


def after_year(year: int) -> RoleFilterFn:
    """Return precondition function that checks if the date is after a given year"""

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return world.get_resource(SimDateTime).year > year

    return fn


def is_gender(gender: Literal["male", "female", "non-binary"]) -> RoleFilterFn:
    """Return precondition function that checks if a character is a given gender"""
    gender_component_types = {"male": Male, "female": Female, "non-binary": NonBinary}

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return gameobject.has_component(gender_component_types[gender])

    return fn


def has_any_work_experience() -> RoleFilterFn:
    """Return True if the character has any work experience at all"""

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return len(gameobject.get_component(WorkHistory)) > 0

    return fn


def has_experience_as_a(
    occupation_type: str, years_experience: int = 0
) -> RoleFilterFn:
    """
    Returns Precondition function that returns true if the character
    has experience as a given occupation type.

    Parameters
    ----------
    occupation_type: str
        The name of the occupation to check for
    years_experience: int
        The number of years of experience the character needs to have

    Returns
    -------
    RoleFilterFn
        The precondition function used when filling the occupation
    """

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        work_history = gameobject.get_component(WorkHistory)
        return (
            work_history.has_experience_as_a(occupation_type)
            and work_history.total_experience_as_a(occupation_type) >= years_experience
        )

    return fn


def is_college_graduate() -> RoleFilterFn:
    """Return True if the character is a college graduate"""

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return gameobject.has_component(CollegeGraduate)

    return fn


def has_component(component_type: Type[Component]) -> RoleFilterFn:
    """Return tru if the gameobject has a component"""

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return gameobject.has_component(component_type)

    return fn
