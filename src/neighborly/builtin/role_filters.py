from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from neighborly.builtin.components import Age, CollegeGraduate, CurrentLocation
from neighborly.core.business import Occupation, Unemployed, WorkHistory
from neighborly.core.character import Gender, GenderValue
from neighborly.core.ecs import GameObject, World
from neighborly.core.query import (
    EcsFindClause,
    IQueryClause,
    QueryContext,
    QueryFilterFn,
    Relation,
)
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


def get_friendships_gt(threshold: float, variables: Tuple[str, str]) -> IQueryClause:
    def clause(ctx: QueryContext, world: World) -> Relation:
        subject, _ = variables

        # loop through each row in the ctx at the given column
        results = []
        for _, row in ctx.relation.get_data_frame().iterrows():
            gameobject = world.get_gameobject(row[subject])
            for r in gameobject.get_component(Relationships).get_all():
                if r.friendship > threshold:
                    results.append((row[subject], r.target))

        values_per_symbol = list(zip(*results))

        if values_per_symbol:
            data = {s: values_per_symbol[i] for i, s in enumerate(variables)}

            if ctx.relation is None:
                return Relation(pd.DataFrame(data))

            return ctx.relation.unify(Relation(pd.DataFrame(data)))

        return Relation.create_empty()

    return clause


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


def get_romances_gt(threshold: float, variables: Tuple[str, str]) -> IQueryClause:
    def clause(ctx: QueryContext, world: World) -> Relation:
        subject, _ = variables

        # loop through each row in the ctx at the given column
        results = []
        for _, row in ctx.relation.get_data_frame().iterrows():
            gameobject = world.get_gameobject(row[subject])
            for r in gameobject.get_component(Relationships).get_all():
                if r.romance > threshold:
                    results.append((row[subject], r.target))

        values_per_symbol = list(zip(*results))

        if values_per_symbol:
            data = {s: values_per_symbol[i] for i, s in enumerate(variables)}

            if ctx.relation is None:
                return Relation(pd.DataFrame(data))

            return ctx.relation.unify(Relation(pd.DataFrame(data)))

        return Relation.create_empty()

    return clause


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


def relationship_has_tags_filter(*tags: str) -> QueryFilterFn:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World, *gameobjects: GameObject) -> bool:

        subject, target = gameobjects
        relationships = subject.get_component(Relationships)
        if target.id in relationships:
            return all([relationships.get(target.id).has_tag(t) for t in tags])
        else:
            return False

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


def is_gender(gender: GenderValue) -> QueryFilterFn:
    """Return precondition function that checks if an entity is a given gender"""

    def fn(world: World, *gameobjects: GameObject) -> bool:
        if gender_component := gameobjects[0].try_component(Gender):
            return gender_component.value == gender
        return False

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
