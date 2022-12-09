from __future__ import annotations

import random
from typing import List, Optional, Tuple

from neighborly.components.business import (
    Business,
    ClosedForBusiness,
    InTheWorkforce,
    Occupation,
    OccupationType,
    OpenForBusiness,
    Services,
    ServiceTypes,
    WorkHistory,
)
from neighborly.components.character import GameCharacter
from neighborly.components.relationship import Relationships
from neighborly.components.routine import Routine, RoutineEntry, RoutinePriority
from neighborly.components.shared import Active, Location, OpenToPublic
from neighborly.core.ecs import GameObject, World
from neighborly.core.event import EventLog
from neighborly.core.query import QueryBuilder
from neighborly.core.status import add_status, get_status, has_status, remove_status
from neighborly.core.time import SimDateTime
from neighborly.events import BusinessClosedEvent, EndJobEvent
from neighborly.statuses.character import Unemployed
from neighborly.utils.common import demolish_building, set_location


def is_unemployed(world: World, *gameobjects: GameObject) -> bool:
    """Query filter that returns true if the character is unemployed"""
    return has_status(gameobjects[0], Unemployed)


def add_coworkers(world: World, character: GameObject, business: GameObject) -> None:
    """Add coworker tags to current coworkers in relationship network"""
    owner = business.get_component(Business).owner
    if owner is not None and owner != character.id:
        character.get_component(Relationships).get(owner).add_tags("Coworker")
        world.get_gameobject(owner).get_component(Relationships).get(
            character.id
        ).add_tags("Coworker")

    for employee_id in business.get_component(Business).get_employees():
        if employee_id == character.id:
            continue

        coworker = world.get_gameobject(employee_id)

        character.get_component(Relationships).get(employee_id).add_tags("Coworker")

        coworker.get_component(Relationships).get(character.id).add_tags("Coworker")


def remove_coworkers(world: World, character: GameObject, business: GameObject) -> None:
    """Remove coworker tags from current coworkers in relationship network"""

    owner = business.get_component(Business).owner
    if owner is not None and owner != character.id:
        character.get_component(Relationships).get(owner).remove_tags("Coworker")
        world.get_gameobject(owner).get_component(Relationships).get(
            character.id
        ).remove_tags("Coworker")

    for employee_id in business.get_component(Business).get_employees():
        if employee_id == character.id:
            continue

        coworker = world.get_gameobject(employee_id)

        character.get_component(Relationships).get(employee_id).remove_tags("Coworker")

        coworker.get_component(Relationships).get(character.id).remove_tags("Coworker")


def shutdown_business(world: World, business: GameObject) -> None:
    """Close a business and remove all employees and the owner"""
    date = world.get_resource(SimDateTime)

    event = BusinessClosedEvent(date, business)

    business.remove_component(OpenForBusiness)
    business.add_component(ClosedForBusiness())

    world.get_resource(EventLog).record_event(event)

    business_comp = business.get_component(Business)
    location = business.get_component(Location)

    # Relocate all GameObjects from at the location
    for entity_id in location.entities:
        entity = world.get_gameobject(entity_id)

        if entity.has_component(GameCharacter):
            # Send all the characters that are present back to their homes
            set_location(
                world,
                entity,
                None,
            )
        else:
            # Delete everything that is not a character
            # assume that it will get lost in the demolition
            world.delete_gameobject(entity_id)

    for employee in business_comp.get_employees():
        end_job(world, world.get_gameobject(employee), reason=event.name)

    if business_comp.owner_type is not None and business_comp.owner is not None:
        end_job(world, world.get_gameobject(business_comp.owner), reason=event.name)

    business.remove_component(Active)
    business.remove_component(OpenToPublic)
    business.remove_component(Location)
    demolish_building(world, business)


def start_job(
    world: World,
    business: Business,
    character: GameObject,
    occupation: Occupation,
    is_owner: bool = False,
) -> None:
    if is_owner:
        business.owner = character.id

    business.add_employee(character.id, occupation.occupation_type)
    character.add_component(occupation)

    add_coworkers(world, character, business.gameobject)

    if has_status(character, Unemployed):
        status = get_status(character, Unemployed).gameobject
        remove_status(character, status)

    character_routine = character.get_component(Routine)
    for day, interval in business.operating_hours.items():
        character_routine.add_entries(
            f"work_@_{business.gameobject.id}",
            [day],
            RoutineEntry(
                start=interval[0],
                end=interval[1],
                location=business.gameobject.id,
                priority=RoutinePriority.MED,
            ),
        )


def end_job(
    world: World,
    character: GameObject,
    reason: str,
) -> None:
    occupation = character.get_component(Occupation)
    business = world.get_gameobject(occupation.business)
    business_comp = business.get_component(Business)

    # Update the former employees relationships
    remove_coworkers(world, character, business)

    if business_comp.owner_type is not None and business_comp.owner == character.id:
        business_comp.set_owner(None)

    business_comp.remove_employee(character.id)

    character.remove_component(Occupation)
    add_status(world, character, Unemployed(30))

    # Update the former employee's work history
    if not character.has_component(WorkHistory):
        character.add_component(WorkHistory())

    character.get_component(WorkHistory).add_entry(
        occupation_type=occupation.occupation_type,
        business=business.id,
        start_date=occupation.start_date,
        end_date=world.get_resource(SimDateTime).copy(),
    )

    # Remove routine entries
    character_routine = character.get_component(Routine)
    for day, _ in business_comp.operating_hours.items():
        character_routine.remove_entries(
            [day],
            f"work_@_{business.id}",
        )

    # Emit the event
    world.get_resource(EventLog).record_event(
        EndJobEvent(
            date=world.get_resource(SimDateTime),
            character=character,
            business=business,
            occupation=occupation.occupation_type,
            reason=reason,
        )
    )


def find_places_with_services(world: World, *services: str) -> List[int]:
    """
    Get all the active locations with the given services

    Parameters
    ----------
    world: World
        The world instance to search within

    services: Tuple[str]
        The services to search for

    Returns
    -------
    The IDs of the matching entities
    """
    matches: List[int] = []
    for gid, services_component in world.get_component(Services):
        if all([services_component.has_service(ServiceTypes.get(s)) for s in services]):
            matches.append(gid)
    return matches


def fill_open_position(
    world: World,
    occupation_type: OccupationType,
    business: Business,
    rng: random.Random,
    candidate: Optional[GameObject] = None,
) -> Optional[Tuple[GameObject, Occupation]]:
    """
    Attempt to find a component entity that meets the preconditions
    for this occupation
    """
    query_builder = (
        QueryBuilder().with_((InTheWorkforce, Active)).filter_(is_unemployed)
    )

    if occupation_type.precondition:
        query_builder.filter_(occupation_type.precondition)

    q = query_builder.build()

    if candidate:
        candidate_list = q.execute(world, Candidate=candidate.id)
    else:
        candidate_list = q.execute(world)

    if candidate_list:
        chosen_candidate = world.get_gameobject(rng.choice(candidate_list)[0])
        return chosen_candidate, Occupation(
            occupation_type=occupation_type.name,
            business=business.gameobject.id,
            level=occupation_type.level,
            start_date=world.get_resource(SimDateTime).copy(),
        )

    return None
