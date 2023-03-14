from __future__ import annotations

from typing import List, Set, Tuple, Type, Union

from neighborly.components.business import Occupation, WorkHistory
from neighborly.components.character import (
    ChildOf,
    Dating,
    Married,
    ParentOf,
    SiblingOf,
)
from neighborly.core.ecs import Component, GameObject
from neighborly.core.ecs.query import QueryClause, QueryContext, Relation, WithClause
from neighborly.core.relationship import Relationship, RelationshipManager
from neighborly.core.status import StatusComponent
from neighborly.core.time import DAYS_PER_YEAR, SimDateTime


def with_components(
    variable: str, component_types: Union[Type[Component], Tuple[Type[Component], ...]]
) -> QueryClause:
    if isinstance(component_types, tuple):
        return WithClause(component_types, variable)
    return WithClause((component_types,), variable)


def with_statuses(
    variable: str, component_types: Union[Type[Component], Tuple[Type[Component], ...]]
) -> QueryClause:
    if isinstance(component_types, tuple):
        return WithClause(component_types, variable)
    return WithClause((component_types,), variable)


def with_relationship(
    owner_var: str,
    target_var: str,
    relationship_var: str,
    *statuses: Type[StatusComponent],
) -> QueryClause:
    def clause(ctx: QueryContext) -> Relation:
        results: List[Tuple[int, int, int]] = []
        for rel_id, relationship in ctx.world.get_component(Relationship):
            r = ctx.world.get_gameobject(rel_id)

            if statuses and not r.has_components(*statuses):
                continue

            results.append((relationship.owner, relationship.target, rel_id))
        return Relation((owner_var, target_var, relationship_var), results)

    return clause


def has_work_experience_as(occupation_type: str, years_experience: int = 0):
    """
    Returns Precondition function that returns true if the entity
    has experience as a given occupation type.

    Parameters
    ----------
    occupation_type: str
        The name of the occupation to check for
    years_experience: int
        The number of years of experience the entity needs to have
    """

    def fn(gameobject: GameObject) -> bool:
        total_experience: float = 0

        current_date = gameobject.world.get_resource(SimDateTime)

        work_history = gameobject.try_component(WorkHistory)

        if work_history is None:
            return False

        for entry in work_history.entries[:-1]:
            if entry.occupation_type == occupation_type:
                total_experience += entry.years_held

        if gameobject.has_component(Occupation):
            occupation = gameobject.get_component(Occupation)
            if occupation.occupation_type == occupation_type:
                total_experience += (
                    float((current_date - occupation.start_date).total_days)
                    / DAYS_PER_YEAR
                )

        return total_experience >= years_experience

    return fn


def has_any_work_experience(years_experience: int = 0):
    """
    Returns Precondition function that returns true if the entity
    has experience as a given occupation type.

    Parameters
    ----------
    years_experience: int
        The number of years of experience the entity needs to have
    """

    def fn(gameobject: GameObject) -> bool:
        total_experience: float = 0

        current_date = gameobject.world.get_resource(SimDateTime)

        work_history = gameobject.try_component(WorkHistory)

        if work_history is None:
            return False

        for entry in work_history.entries[:-1]:
            total_experience += entry.years_held

            if total_experience >= years_experience:
                return True

        if gameobject.has_component(Occupation):
            occupation = gameobject.get_component(Occupation)
            total_experience += (
                float((current_date - occupation.start_date).total_days) / DAYS_PER_YEAR
            )

        return total_experience >= years_experience

    return fn


def is_single(gameobject: GameObject) -> bool:
    """Return true if the character is not dating or married"""
    world = gameobject.world
    for rel_id in gameobject.get_component(RelationshipManager):
        relationship = world.get_gameobject(rel_id)
        if relationship.has_component(Dating) or relationship.has_component(Married):
            return False
    return True


def is_married(gameobject: GameObject) -> bool:
    """Return true if the character is not dating or married"""
    world = gameobject.world
    for rel_id in gameobject.get_component(RelationshipManager):
        relationship = world.get_gameobject(rel_id)
        if relationship.has_component(Married):
            return False
    return True


def _get_family_members(
    character: GameObject, degree_of_sep: int = 2
) -> Set[GameObject]:
    world = character.world

    family_status_types = (ChildOf, ParentOf, SiblingOf)

    # Get all familial ties n-degrees of separation from each character
    family_members: Set[GameObject] = {character}

    visited: Set[GameObject] = set()
    character_queue: List[Tuple[int, GameObject]] = [(0, character)]

    while character_queue:

        deg, character = character_queue.pop(0)
        visited.add(character)

        if deg >= degree_of_sep:
            break

        for relationship_id in character.get_component(
            RelationshipManager
        ).relationships.values():
            relationship = world.get_gameobject(relationship_id)
            if any([relationship.has_component(st) for st in family_status_types]):
                family_member = world.get_gameobject(
                    relationship.get_component(Relationship).target
                )

                if family_member not in visited:
                    character_queue.append((deg + 1, family_member))
                    family_members.add(family_member)

    return family_members


def are_related(a: GameObject, b: GameObject, degree_of_sep: int = 2) -> bool:
    return (
        len(
            _get_family_members(a, degree_of_sep).intersection(
                _get_family_members(b, degree_of_sep)
            )
        )
        > 0
    )
