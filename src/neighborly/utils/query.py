from __future__ import annotations

from typing import List, Set, Tuple, Type, Union

from neighborly.components.business import Occupation, WorkHistory
from neighborly.components.character import Dating, Family, Married
from neighborly.ecs import Component, GameObject
from neighborly.query import QueryClause, QueryContext, Relation, WithClause
from neighborly.relationship import Relationship, Relationships
from neighborly.roles import Roles
from neighborly.statuses import IStatus
from neighborly.time import SimDateTime


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
    *statuses: Type[IStatus],
) -> QueryClause:
    def clause(ctx: QueryContext) -> Relation:
        results: List[Tuple[int, int, int]] = []
        for rel_id, relationship in ctx.world.get_component(Relationship):
            r = ctx.world.gameobject_manager.get_gameobject(rel_id)

            if statuses and not r.has_components(*statuses):
                continue

            results.append((relationship.owner.uid, relationship.target.uid, rel_id))
        return Relation((owner_var, target_var, relationship_var), results)

    return clause


def has_work_experience_as(
    occupation_type: Type[Occupation], years_experience: int = 0
):
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

    def fn(gameobject: GameObject) -> bool:
        total_experience: float = 0

        current_date = gameobject.world.resource_manager.get_resource(SimDateTime)

        work_history = gameobject.try_component(WorkHistory)

        if work_history is None:
            return False

        for entry in work_history.entries[:-1]:
            if entry.occupation_type == occupation_type:
                total_experience += entry.years_held

        for occupation in gameobject.get_component(Roles).get_roles_of_type(Occupation):
            if isinstance(occupation, occupation_type):
                total_experience += current_date.year - occupation.start_year

        return total_experience >= years_experience

    return fn


def get_work_experience_as(occupation_type: Type[Occupation]):
    """
    Returns Precondition function that returns true if the entity
    has experience as a given occupation type.

    Parameters
    ----------
    occupation_type
        The name of the occupation to check for
    """

    def fn(gameobject: GameObject) -> float:
        total_experience: float = 0

        current_date = gameobject.world.resource_manager.get_resource(SimDateTime)

        work_history = gameobject.try_component(WorkHistory)

        if work_history is None:
            return False

        for entry in work_history.entries[:-1]:
            if entry.occupation_type == occupation_type:
                total_experience += entry.years_held

        for occupation in gameobject.get_component(Roles).get_roles_of_type(Occupation):
            if isinstance(occupation, occupation_type):
                total_experience += current_date.year - occupation.start_year

        return total_experience

    return fn


def has_any_work_experience(years_experience: int = 0):
    """
    Returns Precondition function that returns true if the entity
    has experience as a given occupation type.

    Parameters
    ----------
    years_experience
        The number of years of experience the entity needs to have
    """

    def fn(gameobject: GameObject) -> bool:
        total_experience: float = 0

        current_date = gameobject.world.resource_manager.get_resource(SimDateTime)

        work_history = gameobject.try_component(WorkHistory)

        if work_history is None:
            return False

        for entry in work_history.entries[:-1]:
            total_experience += entry.years_held

            if total_experience >= years_experience:
                return True

        for occupation in gameobject.get_component(Roles).get_roles_of_type(Occupation):
            total_experience += current_date.year - occupation.start_year

        return total_experience >= years_experience

    return fn


def is_single(gameobject: GameObject) -> bool:
    """Return true if the character is not dating or married"""
    for _, relationship in gameobject.get_component(Relationships).outgoing.items():
        if relationship.has_component(Dating) or relationship.has_component(Married):
            return False
    return True


def is_married(gameobject: GameObject) -> bool:
    """Return true if the character is not dating or married"""
    for _, relationship in gameobject.get_component(Relationships).outgoing.items():
        if relationship.has_component(Married):
            return False
    return True


def are_related(a: GameObject, b: GameObject, degree_of_sep: int = 2) -> bool:
    visited: Set[GameObject] = set()
    character_queue: List[Tuple[int, GameObject]] = [(0, a)]

    while character_queue:
        deg, character = character_queue.pop(0)
        visited.add(character)

        if deg >= degree_of_sep:
            break

        if character == b:
            return True

        for target, relationship in character.get_component(
            Relationships
        ).outgoing.items():
            if relationship.has_component(Family):
                if target not in visited:
                    character_queue.append((deg + 1, target))

    return False
