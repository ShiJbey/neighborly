from __future__ import annotations

import logging
from typing import List, Optional, Tuple, cast

import numpy as np

from neighborly.builtin.components import (
    Adult,
    CanGetPregnant,
    Child,
    CurrentLocation,
    Elder,
    Female,
    LocationAliases,
    Male,
    NonBinary,
    Teen,
    YoungAdult,
)
from neighborly.core.activity import Activities, ActivityLibrary
from neighborly.core.archetypes import CharacterArchetype, CharacterArchetypeLibrary
from neighborly.core.building import Building
from neighborly.core.business import (
    Business,
    ClosedForBusiness,
    InTheWorkforce,
    Occupation,
    Unemployed,
    WorkHistory,
)
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent, LifeEventLog, Role
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.relationship import (
    Relationship,
    RelationshipGraph,
    RelationshipTag,
)
from neighborly.core.residence import Residence, Resident
from neighborly.core.time import SimDateTime
from neighborly.core.town import LandGrid

logger = logging.getLogger(__name__)


def at_same_location(a: GameObject, b: GameObject) -> bool:
    """Return True if these characters are at the same location"""
    a_location = a.get_component(CurrentLocation).location
    b_location = b.get_component(CurrentLocation).location
    return (
        a_location is not None and b_location is not None and a_location == b_location
    )


def get_top_activities(character_values: PersonalValues, n: int = 3) -> Tuple[str, ...]:
    """Return the top activities a entity would enjoy given their values"""

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
    locations: List[Tuple[int, List[Location, Activities]]] = world.get_components(
        Location, Activities
    )

    matches: List[int] = []

    for location_id, (_, activities_comp) in locations:
        if all([activities_comp.has_activity(a) for a in activities]):
            matches.append(location_id)

    return matches


def find_places_with_any_activities(world: World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have any of the given activities

    Results are sorted by how many activities they match
    """

    flags = ActivityLibrary.get_flags(*activities)

    def score_location(act_comp: Activities) -> int:
        return sum([act_comp.has_activity(a) for a in activities])

    locations: List[Tuple[int, List[Location, Activities]]] = world.get_components(
        Location, Activities
    )

    matches: List[Tuple[int, int]] = []

    for location_id, (_, activities_comp) in locations:
        score = score_location(activities_comp)
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


def move_to_location(world: World, gameobject: GameObject, destination_id: int) -> None:
    # A location cant move to itself
    if destination_id == gameobject.id:
        return

    # Check if they
    current_location_comp = gameobject.try_component(CurrentLocation)

    if current_location_comp is not None:
        current_location = world.get_gameobject(
            current_location_comp.location
        ).get_component(Location)
    else:
        gameobject.add_component(CurrentLocation)

    if character.location is not None:

        current_location.remove_entity(character.gameobject.id)

    destination.add_entity(gameobject.id)
    character.location = destination.gameobject.id


def get_locations(world: World) -> List[Tuple[int, Location]]:
    return sorted(
        cast(List[Tuple[int, Location]], world.get_component(Location)),
        key=lambda pair: pair[0],
    )


def move_residence(character: GameCharacter, new_residence: Residence) -> None:
    """Move a entity into a residence"""

    world = character.gameobject.world
    location_aliases = character.gameobject.get_component(LocationAliases)

    # Move out of the old residence
    if "home" in location_aliases.aliases:
        old_residence = world.get_gameobject(
            location_aliases.aliases["home"]
        ).get_component(Residence)
        old_residence.remove_resident(character.gameobject.id)
        if old_residence.is_owner(character.gameobject.id):
            old_residence.remove_owner(character.gameobject.id)

    # Move into new residence
    new_residence.add_resident(character.gameobject.id)
    location_aliases.aliases["home"] = new_residence.gameobject.id
    character.gameobject.add_component(Resident(new_residence.gameobject.id))


############################################
# GENERATING CHARACTERS OF DIFFERENT AGES
############################################


def choose_gender(engine: NeighborlyEngine, character: GameCharacter) -> None:
    if character.gameobject.has_component(CanGetPregnant):
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
    Create a new Young-adult-aged entity

    Parameters
    ----------
    world: World
        The world to spawn the entity into
    engine: NeighborlyEngine
        The engine instance that holds the entity archetypes
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


def demolish_building(gameobject: GameObject) -> None:
    """Remove the building component and free the land grid space"""
    world = gameobject.world
    gameobject.remove_component(Building)
    position = gameobject.get_component(Position2D)
    land_grid = world.get_resource(LandGrid)
    land_grid[int(position.x), int(position.y)] = None
    logger.debug(f"Demolished building at {str(position)}")


def close_for_business(business: Business) -> None:
    """Close a business and remove all employees and the owner"""
    world = business.gameobject.world
    date = world.get_resource(SimDateTime)

    business.gameobject.add_component(ClosedForBusiness())

    close_for_business_event = LifeEvent(
        name="ClosedForBusiness",
        timestamp=date.to_date_str(),
        roles=[
            Role("Business", business.gameobject.id),
        ],
    )

    world.get_resource(LifeEventLog).record_event(close_for_business_event)

    for employee in business.get_employees():
        layoff_employee(business, world.get_gameobject(employee))

    if business.owner_type is not None:
        layoff_employee(business, world.get_gameobject(business.owner))
        business.owner = None


def layoff_employee(business: Business, employee: GameObject) -> None:
    """Remove an employee"""
    world = business.gameobject.world
    date = world.get_resource(SimDateTime)
    business.remove_employee(employee.id)

    occupation = employee.get_component(Occupation)

    fired_event = LifeEvent(
        name="LaidOffFromJob",
        timestamp=date.to_date_str(),
        roles=[
            Role("Business", business.gameobject.id),
            Role("Character", employee.id),
        ],
    )

    world.get_resource(LifeEventLog).record_event(fired_event)

    employee.get_component(WorkHistory).add_entry(
        occupation_type=occupation.occupation_type,
        business=business.gameobject.id,
        start_date=occupation.start_date,
        end_date=date.copy(),
        reason_for_leaving=fired_event,
    )

    employee.remove_component(Occupation)


def choose_random_character_archetype(
    engine: NeighborlyEngine,
) -> Optional[CharacterArchetype]:
    """Performs a weighted random selection across all character archetypes"""
    archetype_choices: List[CharacterArchetype] = []
    archetype_weights: List[int] = []

    for archetype in CharacterArchetypeLibrary.get_all():
        archetype_choices.append(archetype)
        archetype_weights.append(archetype.spawn_multiplier)

    if archetype_choices:
        # Choose an archetype at random
        archetype: CharacterArchetype = engine.rng.choices(
            population=archetype_choices, weights=archetype_weights, k=1
        )[0]

        return archetype
    else:
        return None
