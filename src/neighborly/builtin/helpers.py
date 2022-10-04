from __future__ import annotations

import logging
from typing import List, Optional, Tuple, cast

import numpy as np

from neighborly.builtin.statuses import (
    Adult,
    Child,
    Elder,
    Female,
    Male,
    NonBinary,
    Teen,
    YoungAdult,
)
from neighborly.core.activity import ActivityLibrary
from neighborly.core.archetypes import CharacterArchetype
from neighborly.core.business import Business, InTheWorkforce, Unemployed
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.relationship import (
    Relationship,
    RelationshipGraph,
    RelationshipTag,
)
from neighborly.core.residence import Residence, Resident

logger = logging.getLogger(__name__)


def get_top_activities(character_values: PersonalValues, n: int = 3) -> Tuple[str, ...]:
    """Return the top activities a character would enjoy given their values"""

    scores: List[Tuple[int, str]] = []

    for activity in ActivityLibrary.get_all():
        score: int = int(np.dot(character_values.traits, activity.personal_values))
        scores.append((score, activity.name))

    return tuple(
        [
            activity_score[1]
            for activity_score in sorted(scores, key=lambda s: s[0], reverse=True)
        ][:n]
    )


def find_places_with_activities(world: World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have the given activities"""
    locations = world.get_component(Location)

    matches: List[int] = []

    for location_id, location in locations:
        if location.has_flags(*ActivityLibrary.get_flags(*activities)):
            matches.append(location_id)

    return matches


def find_places_with_any_activities(world: World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have any of the given activities

    Results are sorted by how many activities they match
    """

    flags = ActivityLibrary.get_flags(*activities)

    def score_location(loc: Location) -> int:
        location_score: int = 0
        for flag in flags:
            if loc.activity_flags & flag > 0:
                location_score += 1
        return location_score

    locations = world.get_component(Location)

    matches: List[Tuple[int, int]] = []

    for location_id, location in locations:
        score = score_location(location)
        if score > 0:
            matches.append((score, location_id))

    return [match[1] for match in sorted(matches, key=lambda m: m[0], reverse=True)]


def add_coworkers(character: GameObject, business: Business) -> None:
    """Add coworker tags to current coworkers in relationship network"""

    world: World = character.world
    rel_graph = world.get_resource(RelationshipGraph)

    for employee_id in business.get_employees():
        if employee_id == character.id:
            continue

        if not rel_graph.has_connection(character.id, employee_id):
            rel_graph.add_relationship(Relationship(character.id, employee_id))

        if not rel_graph.has_connection(employee_id, character.id):
            rel_graph.add_relationship(Relationship(employee_id, character.id))

        rel_graph.get_connection(character.id, employee_id).add_tags(
            RelationshipTag.Coworker
        )

        rel_graph.get_connection(employee_id, character.id).add_tags(
            RelationshipTag.Coworker
        )


def remove_coworkers(character: GameObject, business: Business) -> None:
    """Remove coworker tags from current coworkers in relationship network"""
    world = character.world
    rel_graph = world.get_resource(RelationshipGraph)

    for employee_id in business.get_employees():
        if employee_id == character.id:
            continue

        if rel_graph.has_connection(character.id, employee_id):
            rel_graph.get_connection(character.id, employee_id).remove_tags(
                RelationshipTag.Coworker
            )

        if rel_graph.has_connection(employee_id, character.id):
            rel_graph.get_connection(employee_id, character.id).remove_tags(
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


def move_residence(character: GameCharacter, new_residence: Residence) -> None:
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

    # Move into new residence
    new_residence.add_resident(character.gameobject.id)
    character.location_aliases["home"] = new_residence.gameobject.id
    character.gameobject.add_component(Resident(new_residence.gameobject.id))


############################################
# GENERATING CHARACTERS OF DIFFERENT AGES
############################################


def choose_gender(engine: NeighborlyEngine, character: GameCharacter) -> None:
    if character.can_get_pregnant:
        gender_type = engine.rng.choice([Female, NonBinary])
        character.gameobject.add_component(gender_type())
    else:
        gender_type = engine.rng.choice([Male, NonBinary])
        character.gameobject.add_component(gender_type())


def generate_child_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
) -> GameObject:
    gameobject = world.spawn_archetype(archetype)
    gameobject.add_component(Child())
    character = gameobject.get_component(GameCharacter)

    choose_gender(engine, character)

    # generate an age
    character.age = engine.rng.randint(
        0, character.character_def.life_stages["teen"] - 1
    )

    return gameobject


def generate_teen_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
) -> GameObject:
    gameobject = world.spawn_archetype(archetype)
    gameobject.add_component(Teen())
    character = gameobject.get_component(GameCharacter)
    choose_gender(engine, character)
    character.age = engine.rng.randint(
        character.character_def.life_stages["teen"],
        character.character_def.life_stages["young_adult"] - 1,
    )

    return gameobject


def generate_young_adult_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
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
    gameobject = world.spawn_archetype(archetype)
    gameobject.add_component(Unemployed())
    gameobject.add_component(YoungAdult())
    gameobject.add_component(Adult())
    gameobject.add_component(InTheWorkforce())
    character = gameobject.get_component(GameCharacter)
    choose_gender(engine, character)
    character.age = engine.rng.randint(
        character.character_def.life_stages["young_adult"],
        character.character_def.life_stages["adult"] - 1,
    )
    return gameobject


def generate_adult_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
) -> GameObject:
    gameobject = world.spawn_archetype(archetype)
    gameobject.add_component(Unemployed())
    gameobject.add_component(Adult())
    gameobject.add_component(InTheWorkforce())
    character = gameobject.get_component(GameCharacter)
    choose_gender(engine, character)
    character.age = engine.rng.randint(
        character.character_def.life_stages["adult"],
        character.character_def.life_stages["elder"] - 1,
    )
    return gameobject


def generate_elderly_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
) -> GameObject:
    gameobject = world.spawn_archetype(archetype)
    gameobject.add_component(Elder())
    gameobject.add_component(Adult())
    gameobject.add_component(InTheWorkforce())
    character = gameobject.get_component(GameCharacter)
    choose_gender(engine, character)
    character.age = engine.rng.randint(
        character.character_def.life_stages["elder"],
        character.character_def.lifespan - 1,
    )
    return gameobject
