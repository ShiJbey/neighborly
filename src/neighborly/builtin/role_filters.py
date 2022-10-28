from __future__ import annotations

from typing import Any, Literal, Type

from neighborly.builtin.components import Age, CollegeGraduate, Female, Male, NonBinary
from neighborly.core.business import Occupation, Unemployed, WorkHistory
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.life_event import RoleFilterFn
from neighborly.core.relationship import RelationshipGraph
from neighborly.core.time import SimDateTime


def over_age(age: int) -> RoleFilterFn:
    def fn(world: World, gameobject: GameObject, **kwargs) -> bool:
        age_component = gameobject.try_component(Age)
        if age_component is not None:
            return age_component.value > age

    return fn


def is_man(world: World, gameobject: GameObject, **kwargs) -> bool:
    """Return true if GameObject is a man"""
    return gameobject.has_component(Male)


def is_single(world: World, gameobject: GameObject, **kwargs) -> bool:
    """Return True if this entity has no relationships tagged as significant others"""
    rel_graph = world.get_resource(RelationshipGraph)
    marriages = rel_graph.get_all_relationships_with_tags(gameobject.id, "Married")
    dating_relationships = rel_graph.get_all_relationships_with_tags(
        gameobject.id, "Dating"
    )

    return len(marriages) == 0 and len(dating_relationships) == 0
    # return gameobject.has_component(IsSingle)


def is_unemployed(world: World, gameobject: GameObject, **kwargs) -> bool:
    """Returns True if this entity does not have a job"""
    # return (
    #     not gameobject.has_component(Occupation)
    #     and gameobject.has_component(InTheWorkforce)
    #     and not gameobject.has_component(Retired)
    # )
    return gameobject.has_component(Unemployed)


def is_employed(world: World, gameobject: GameObject, **kwargs) -> bool:
    """Returns True if this entity has a job"""
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
    """Return precondition function that checks if an entity is a given gender"""
    gender_component_types = {"male": Male, "female": Female, "non-binary": NonBinary}

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return gameobject.has_component(gender_component_types[gender])

    return fn


def has_any_work_experience() -> RoleFilterFn:
    """Return True if the entity has any work experience at all"""

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return len(gameobject.get_component(WorkHistory)) > 0

    return fn


def has_experience_as_a(
    occupation_type: str, years_experience: int = 0
) -> RoleFilterFn:
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
    RoleFilterFn
        The precondition function used when filling the occupation
    """

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        total_experience: int = 0

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


def is_college_graduate() -> RoleFilterFn:
    """Return True if the entity is a college graduate"""

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return gameobject.has_component(CollegeGraduate)

    return fn


def has_component(component_type: Type[Component]) -> RoleFilterFn:
    """Return tru if the gameobject has a component"""

    def fn(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return gameobject.has_component(component_type)

    return fn
