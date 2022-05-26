from __future__ import annotations

from typing import cast

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.business import Business
from neighborly.core.location import Location
from neighborly.core.relationship import Relationship, RelationshipTag
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.tags import Tag


def hire_character_at_business(character: GameObject, **kwargs) -> None:
    """Hire a character at a given business"""
    ...


def add_employee(business: GameObject, **kwargs) -> None:
    """Add an employee to the given business"""
    ...


def remove_employee(business: GameObject, **kwargs) -> None:
    """Add an employee to the given business"""
    ...


def add_coworkers(character: GameObject, **kwargs) -> None:
    """Add coworker tags to current coworkers in relationship network"""
    business: GameObject = kwargs["business"]
    business_comp = business.get_component(Business)
    world: World = kwargs["world"]

    relationship_net = world.get_resource(RelationshipNetwork)

    for employee_id in business_comp.get_employees():
        if employee_id == character.id:
            continue

        if not relationship_net.has_connection(character.id, employee_id):
            relationship_net.add_connection(
                character.id, employee_id, Relationship(character.id, employee_id)
            )

        relationship_net.get_connection(character.id, employee_id).add_tags(
            RelationshipTag.Coworker
        )


def remove_coworkers(character: GameObject, **kwargs) -> None:
    """Remove coworker tags from current coworkers in relationship network"""
    business: GameObject = kwargs["business"]
    business_comp = business.get_component(Business)
    world: World = kwargs["world"]

    relationship_net = world.get_resource(RelationshipNetwork)

    for employee_id in business_comp.get_employees():
        if employee_id == character.id:
            continue

        if relationship_net.has_connection(character.id, employee_id):
            relationship_net.get_connection(character.id, employee_id).remove_tags(
                RelationshipTag.Coworker
            )


def add_tag(character: GameCharacter, tag: Tag) -> None:
    if tag.name in character.tags:
        raise RuntimeError("Cannot add duplicate tags")
    character.tags[tag.name] = tag


def remove_tag(character: GameCharacter, tag: Tag) -> None:
    if tag.name in character.tags:
        raise RuntimeError("Cannot add duplicate tags")
    del character.tags[tag.name]


def move_character(world: World, character_id: int, location_id: int) -> None:
    destination: Location = world.get_gameobject(location_id).get_component(Location)
    character: GameCharacter = world.get_gameobject(character_id).get_component(
        GameCharacter
    )

    if location_id == character.location:
        return

    if character.location is not None:
        current_location: Location = world.get_gameobject(
            character.location
        ).get_component(Location)
        current_location.remove_character(character_id)

    destination.add_character(character_id)
    character.location = location_id


def get_locations(world: World) -> list[tuple[int, Location]]:
    return sorted(
        cast(list[tuple[int, Location]], world.get_component(Location)),
        key=lambda pair: pair[0],
    )


def add_relationship_tag(
    world: World, owner_id: int, target_id: int, tag: RelationshipTag
) -> None:
    """Add a relationship modifier on the subject's relationship to the target"""
    world.get_resource(RelationshipNetwork).get_connection(
        owner_id, target_id
    ).add_tags(tag)
