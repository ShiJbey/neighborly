from __future__ import annotations

import logging
from typing import List, Optional, Tuple, cast

import numpy as np

import neighborly.core.behavior_tree as bt
from neighborly.builtin.statuses import (
    Adult,
    Child,
    CollegeGraduate,
    Elder,
    InTheWorkforce,
    Teen,
    Unemployed,
    YoungAdult,
)
from neighborly.core.activity import ActivityLibrary
from neighborly.core.archetypes import CharacterArchetype
from neighborly.core.business import Business
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import EventRole, LifeEvent, LifeEventLog
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.relationship import (
    Relationship,
    RelationshipGraph,
    RelationshipTag,
)
from neighborly.core.residence import Residence, Resident
from neighborly.core.time import SimDateTime

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
        old_residence.gameobject.get_component(Location).whitelist.remove(
            character.gameobject.id
        )

    # Move into new residence
    new_residence.add_resident(character.gameobject.id)
    character.location_aliases["home"] = new_residence.gameobject.id
    new_residence.gameobject.get_component(Location).whitelist.add(
        character.gameobject.id
    )
    character.gameobject.add_component(Resident(new_residence.gameobject.id))


############################################
# GENERATING CHARACTERS OF DIFFERENT AGES
############################################


def generate_child_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
) -> GameObject:
    character = world.spawn_archetype(archetype)
    character.add_component(Child())
    return character


def generate_teen_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
) -> GameObject:
    character = world.spawn_archetype(archetype)
    character.add_component(Teen())
    return character


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
    character = world.spawn_archetype(archetype)
    character.add_component(Unemployed())
    character.add_component(YoungAdult())
    character.add_component(InTheWorkforce())
    return character


def generate_adult_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
) -> GameObject:
    character = world.spawn_archetype(archetype)
    character.add_component(Unemployed())
    character.add_component(Adult())
    character.add_component(InTheWorkforce())
    return character


def generate_elderly_character(
    world: World, engine: NeighborlyEngine, archetype: CharacterArchetype
) -> GameObject:
    character = world.spawn_archetype(archetype)
    character.add_component(Elder())
    character.add_component(InTheWorkforce())
    return character


############################################
# Actions
############################################


def become_adult_behavior(chance_depart: float) -> bt.BehaviorNode:
    return bt.sequence(chance_node(chance_depart), depart_action)


def chance_node(chance: float) -> bt.BehaviorNode:
    """Returns BehaviorTree node that returns True with a given probability"""

    def fn(world: World, event: LifeEvent, **kwargs) -> bool:
        return world.get_resource(NeighborlyEngine).rng.random() < chance

    return fn


def action_node(fn) -> bt.BehaviorNode:
    def wrapper(world: World, event: LifeEvent, **kwargs) -> bool:
        fn(world, event, **kwargs)
        return True

    return wrapper


@action_node
def go_to_college(world: World, event: LifeEvent, **kwargs) -> None:
    gameobject = world.get_gameobject(event["Unemployed"])
    gameobject.add_component(CollegeGraduate())
    # Reset the unemployment counter since they graduate from school
    gameobject.get_component(Unemployed).duration_days = 0

    world.get_resource(LifeEventLog).record_event(
        LifeEvent(
            name="GraduatedCollege",
            roles=[EventRole("Graduate", gameobject.id)],
            timestamp=world.get_resource(SimDateTime).to_iso_str(),
        )
    )


@action_node
def death_action(world: World, event: LifeEvent, **kwargs) -> None:
    gameobject = world.get_gameobject(event["Deceased"])
    gameobject.archive()

    world.get_resource(LifeEventLog).record_event(
        LifeEvent(
            name="Death",
            roles=[EventRole("Deceased", gameobject.id)],
            timestamp=world.get_resource(SimDateTime).to_iso_str(),
        )
    )


@action_node
def depart_action(world: World, event: LifeEvent, **kwargs) -> None:
    gameobject = world.get_gameobject(event["Departee"])
    gameobject.archive()

    # Get the character's dependent nuclear family
    rel_graph = world.get_resource(RelationshipGraph)

    spouse_rel = rel_graph.get_all_relationships_with_tags(
        gameobject.id, RelationshipTag.Spouse
    )

    if spouse_rel:
        world.get_gameobject(spouse_rel[0].target).archive()
        event.roles.append(EventRole("Departee", spouse_rel[0].target))

    children = rel_graph.get_all_relationships_with_tags(
        gameobject.id, RelationshipTag.Child | RelationshipTag.NuclearFamily
    )
    for child_rel in children:
        world.get_gameobject(child_rel.target).archive()
        event.roles.append(EventRole("Departee", child_rel.target))

    world.get_resource(LifeEventLog).record_event(
        LifeEvent(
            name="Depart",
            roles=event.roles,
            timestamp=world.get_resource(SimDateTime).to_iso_str(),
        )
    )
