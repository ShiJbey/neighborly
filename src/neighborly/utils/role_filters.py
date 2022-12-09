from __future__ import annotations

from typing import List, Tuple, Type

from neighborly.components.business import Occupation, WorkHistory
from neighborly.components.character import (
    CollegeGraduate,
    Gender,
    GenderValue,
    LifeStage,
    LifeStageValue,
)
from neighborly.components.relationship import Relationships
from neighborly.components.shared import Age, CurrentLocation
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.query import QueryContext, QueryFilterFn, QueryGetFn
from neighborly.core.time import SimDateTime
from neighborly.statuses.character import Unemployed


def friendship_gte(threshold: float) -> QueryFilterFn:
    """
    Filter function for an ECS query that returns True if the friendship
    value from one character to another is greater than or equal to a given threshold
    """

    def precondition(world: World, *gameobjects: GameObject) -> bool:
        if relationships := gameobjects[0].try_component(Relationships):
            return (
                gameobjects[1].id in relationships
                and relationships.get(gameobjects[1].id).friendship.value >= threshold
            )
        return False

    return precondition


def friendship_lte(threshold: float) -> QueryFilterFn:
    """
    Filter function for an ECS query that returns True if the friendship
    value from one character to another is less than or equal to a given threshold
    """

    def precondition(world: World, *gameobjects: GameObject) -> bool:
        if relationships := gameobjects[0].try_component(Relationships):
            return (
                gameobjects[1].id in relationships
                and relationships.get(gameobjects[1].id).friendship.value <= threshold
            )
        return False

    return precondition


def romance_gte(threshold: float) -> QueryFilterFn:
    """
    Filter function for an ECS query that returns True if the romance
    value from one character to another is greater than or equal to a given threshold
    """

    def precondition(world: World, *gameobjects: GameObject) -> bool:
        if relationships := gameobjects[0].try_component(Relationships):
            return (
                gameobjects[1].id in relationships
                and relationships.get(gameobjects[1].id).romance.value >= threshold
            )
        return False

    return precondition


def romance_lte(threshold: float) -> QueryFilterFn:
    """
    Filter function for an ECS query that returns True if the romance
    value from one character to another is less than or equal to a given threshold
    """

    def precondition(world: World, *gameobjects: GameObject) -> bool:
        if relationships := gameobjects[0].try_component(Relationships):
            return (
                gameobjects[1].id in relationships
                and relationships.get(gameobjects[1].id).romance.value <= threshold
            )
        return False

    return precondition


def get_friendships_gte(threshold: float) -> QueryGetFn:
    """
    Returns QueryGetFn that finds all the relationships of the first variable that have
    friendship scores greater than or equal to the threshold and binds them to the
    second variable
    """

    def clause(
        ctx: QueryContext, world: World, *variables: str
    ) -> List[Tuple[int, ...]]:
        subject, _ = variables

        # loop through each row in the ctx at the given column
        results: List[Tuple[int, ...]] = []
        for _, row in ctx.relation.get_data_frame().iterrows():  # type: ignore
            gameobject = world.get_gameobject(row[subject])  # type: ignore
            for r in gameobject.get_component(Relationships).get_all():
                if r.friendship >= threshold:
                    results.append((row[subject], r.target))  # type: ignore

        return results

    return clause


def get_friendships_lte(threshold: float) -> QueryGetFn:
    """
    Returns QueryGetFn that finds all the relationships of the first variable that have
    friendship scores less than or equal to the threshold and binds them to the
    second variable
    """

    def clause(
        ctx: QueryContext, world: World, *variables: str
    ) -> List[Tuple[int, ...]]:
        subject, _ = variables

        # loop through each row in the ctx at the given column
        results: List[Tuple[int, ...]] = []
        for _, row in ctx.relation.get_data_frame().iterrows():  # type: ignore
            gameobject = world.get_gameobject(row[subject])  # type: ignore
            for r in gameobject.get_component(Relationships).get_all():
                if r.friendship <= threshold:
                    results.append((row[subject], r.target))  # type: ignore

        return results

    return clause


def get_romances_gte(threshold: float) -> QueryGetFn:
    """
    Returns QueryGetFn that finds all the relationships of the first variable that have
    romance scores greater than or equal to the threshold and binds them to the
    second variable
    """

    def clause(
        ctx: QueryContext, world: World, *variables: str
    ) -> List[Tuple[int, ...]]:
        subject, _ = variables

        # loop through each row in the ctx at the given column
        results: List[Tuple[int, ...]] = []
        for _, row in ctx.relation.get_data_frame().iterrows():  # type: ignore
            gameobject = world.get_gameobject(row[subject])  # type: ignore
            for r in gameobject.get_component(Relationships).get_all():
                if r.romance >= threshold:
                    results.append((row[subject], r.target))  # type: ignore

        return results

    return clause


def get_romances_lte(threshold: float) -> QueryGetFn:
    """
    Returns QueryGetFn that finds all the relationships of the first variable that have
    romance scores less than or equal to the threshold and binds them to the
    second variable
    """

    def clause(
        ctx: QueryContext, world: World, *variables: str
    ) -> List[Tuple[int, ...]]:
        subject, _ = variables

        # loop through each row in the ctx at the given column
        results: List[Tuple[int, ...]] = []
        for _, row in ctx.relation.get_data_frame().iterrows():  # type: ignore
            gameobject = world.get_gameobject(row[subject])  # type: ignore
            for r in gameobject.get_component(Relationships).get_all():
                if r.romance <= threshold:
                    results.append((row[subject], r.target))  # type: ignore

        return results

    return clause


def relationship_has_tags(*tags: str) -> QueryFilterFn:
    """
    Query filter function that returns true if the first of the given game
    objects has a relationship toward the second game object with the given
    tags
    """

    def precondition(world: World, *gameobjects: GameObject) -> bool:

        subject, target = gameobjects
        relationships = subject.get_component(Relationships)
        if target.id in relationships:
            return all([relationships.get(target.id).has_tag(t) for t in tags])
        else:
            return False

    return precondition


def get_relationships_with_tags(*tags: str) -> QueryGetFn:
    """
    Returns a list of all the GameObjects with the given component
    """

    def fn(ctx: QueryContext, world: World, *variables: str) -> List[Tuple[int, ...]]:
        subject, _ = variables

        # loop through each row in the ctx at the given column
        results: List[Tuple[int, ...]] = []
        for _, row in ctx.relation.get_data_frame().iterrows():  # type: ignore
            gameobject = world.get_gameobject(row[subject])  # type: ignore
            for r in gameobject.get_component(Relationships).get_all():
                if all([r.has_tag(t) for t in tags]):
                    results.append((row[subject], r.target))  # type: ignore

        return results

    return fn


def at_same_location(world: World, *gameobjects: GameObject) -> bool:
    """Return True if these characters are at the same location"""
    a_location = gameobjects[0].try_component(CurrentLocation)
    b_location = gameobjects[1].try_component(CurrentLocation)
    return (
        a_location is not None
        and b_location is not None
        and a_location.location == b_location.location
    )


def life_stage_eq(stage: LifeStageValue) -> QueryFilterFn:
    def fn(world: World, *gameobjects: GameObject) -> bool:
        life_stage = gameobjects[0].try_component(LifeStage)
        if life_stage is not None:
            return life_stage.stage == stage
        return False

    return fn


def life_stage_ge(stage: LifeStageValue) -> QueryFilterFn:
    def fn(world: World, *gameobjects: GameObject) -> bool:
        life_stage = gameobjects[0].try_component(LifeStage)
        if life_stage is not None:
            return life_stage.stage >= stage
        return False

    return fn


def life_stage_le(stage: LifeStageValue) -> QueryFilterFn:
    def fn(world: World, *gameobjects: GameObject) -> bool:
        life_stage = gameobjects[0].try_component(LifeStage)
        if life_stage is not None:
            return life_stage.stage <= stage
        return False

    return fn


def over_age(age: int) -> QueryFilterFn:
    def fn(world: World, *gameobjects: GameObject) -> bool:
        age_component = gameobjects[0].try_component(Age)
        if age_component is not None:
            return age_component.value > age
        return False

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


def has_component(component_type: Type[Component]) -> QueryFilterFn:
    """Return True if the entity has a given component type"""

    def precondition(world: World, *gameobject: GameObject) -> bool:
        return gameobject[0].has_component(component_type)

    return precondition
