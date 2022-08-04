from __future__ import annotations

from typing import List, Tuple, cast, Optional

from neighborly.builtin.statuses import Child, Teen, Unemployed, YoungAdult, Adult, Elder
from neighborly.core.business import Business
from neighborly.core.character import GameCharacter, CharacterArchetype
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.relationship import Relationship, RelationshipTag, RelationshipGraph
from neighborly.core.residence import Residence, Resident


def add_coworkers(character: GameObject, **kwargs) -> None:
    """Add coworker tags to current coworkers in relationship network"""
    business: GameObject = kwargs["business"]
    business_comp = business.get_component(Business)
    world: World = kwargs["world"]

    rel_graph = world.get_resource(RelationshipGraph)

    for employee_id in business_comp.get_employees():
        if employee_id == character.id:
            continue

        if not rel_graph.has_connection(character.id, employee_id):
            rel_graph.add_connection(
                character.id, employee_id, Relationship(character.id, employee_id)
            )

        rel_graph.get_connection(character.id, employee_id).add_tags(
            RelationshipTag.Coworker
        )


def remove_coworkers(character: GameObject, **kwargs) -> None:
    """Remove coworker tags from current coworkers in relationship network"""
    business: GameObject = kwargs["business"]
    business_comp = business.get_component(Business)
    world: World = kwargs["world"]

    rel_graph = world.get_resource(RelationshipGraph)

    for employee_id in business_comp.get_employees():
        if employee_id == character.id:
            continue

        if rel_graph.has_connection(character.id, employee_id):
            rel_graph.get_connection(character.id, employee_id).remove_tags(
                RelationshipTag.Coworker
            )


def move_to_location(
    world: World, character: GameCharacter, destination: Location
) -> None:
    if destination.gameobject.id == character.location:
        return

    if character.location is not None:
        current_location: Location = world.get_gameobject(
            character.location
        ).get_component(Location)
        current_location.remove_character(character.gameobject.id)

    destination.add_character(character.gameobject.id)
    character.location = destination.gameobject.id


def get_locations(world: World) -> List[Tuple[int, Location]]:
    return sorted(
        cast(List[Tuple[int, Location]], world.get_component(Location)),
        key=lambda pair: pair[0],
    )


def move_residence(character: GameCharacter, residence: Residence) -> None:
    """Move a character into a residence"""

    world = character.gameobject.world

    # Move out of the old residence
    if "home" in character.location_aliases:
        old_residence = world.get_gameobject(
            character.location_aliases["home"]
        ).get_component(Residence)
        old_residence.remove_resident(character.gameobject.id)
        if old_residence.is_owner(character.gameobject.id):
            old_residence.remove_owner(character.gameobject.id)
        old_residence.gameobject.get_component(Location).whitelist.remove(
            character.gameobject.id
        )

    # Move into new residence
    residence.add_resident(character.gameobject.id)
    character.location_aliases["home"] = residence.gameobject.id
    residence.gameobject.get_component(Location).whitelist.add(character.gameobject.id)
    character.gameobject.add_component(Resident(residence.gameobject.id))


def generate_child_character(
    world: World,
    engine: NeighborlyEngine,
    archetype: CharacterArchetype
) -> GameObject:
    character = world.spawn_archetype(archetype)
    character.add_component(Child())
    return character


def generate_teen_character(
    world: World,
    engine: NeighborlyEngine,
    archetype: CharacterArchetype
) -> GameObject:
    character = world.spawn_archetype(archetype)
    character.add_component(Teen())
    return character


def generate_young_adult_character(
    world: World,
    engine: NeighborlyEngine,
    archetype: CharacterArchetype
) -> GameObject:
    """
    Create a new Young-adult-aged character

    Parameters
    ----------
    world: World
        The world to spawn the character into
    engine: NeighborlyEngine
        The engine instance that holds the character archetypes
    archetype: Optional[str]
        The name of the archetype to generate. A random archetype
        will be generated if not provided

    Returns
    -------
    GameObject
        The final generated gameobject
    """
    character = world.spawn_archetype(archetype)
    character.add_component(Unemployed())
    character.add_component(YoungAdult())
    return character


def generate_adult_character(
    world: World,
    engine: NeighborlyEngine,
    archetype: CharacterArchetype
) -> GameObject:
    character = world.spawn_archetype(archetype)
    character.add_component(Unemployed())
    character.add_component(Adult())
    return character


def generate_elderly_character(
    world: World,
    engine: NeighborlyEngine,
    archetype: CharacterArchetype
) -> GameObject:
    character = world.spawn_archetype(archetype)
    character.add_component(Elder())
    return character
