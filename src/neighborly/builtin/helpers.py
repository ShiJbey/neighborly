from __future__ import annotations

import logging
from typing import List, Optional, Union, cast

from neighborly.builtin.archetypes import BaseCharacterArchetype
from neighborly.builtin.components import (
    Active,
    CurrentLocation,
    LocationAliases,
    OpenToPublic,
    Vacant,
)
from neighborly.builtin.events import BusinessClosedEvent, DepartEvent, EndJobEvent
from neighborly.core.archetypes import ICharacterArchetype
from neighborly.core.building import Building
from neighborly.core.business import (
    Business,
    ClosedForBusiness,
    Occupation,
    OpenForBusiness,
    Services,
    ServiceTypes,
    Unemployed,
    WorkHistory,
)
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.event import EventLog
from neighborly.core.inheritable import (
    IInheritable,
    get_inheritable_traits_given_parents,
)
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationships
from neighborly.core.residence import Residence, Resident
from neighborly.core.routine import Routine, RoutineEntry, RoutinePriority
from neighborly.core.settlement import Settlement
from neighborly.core.status import add_status
from neighborly.core.time import SimDateTime

logger = logging.getLogger(__name__)


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


def add_coworkers(world: World, character: GameObject, business: GameObject) -> None:
    """Add coworker tags to current coworkers in relationship network"""
    owner = business.get_component(Business).owner
    if owner is not None and owner != character.id:
        character.get_component(Relationships).get(owner).add_tags("Coworker")

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

    for employee_id in business.get_component(Business).get_employees():
        if employee_id == character.id:
            continue

        coworker = world.get_gameobject(employee_id)

        character.get_component(Relationships).get(employee_id).remove_tags("Coworker")

        coworker.get_component(Relationships).get(character.id).remove_tags("Coworker")


def set_location(
    world: World, gameobject: GameObject, destination: Optional[Union[int, str]]
) -> None:
    if isinstance(destination, str):
        # Check for a location aliases component
        if location_aliases := gameobject.try_component(LocationAliases):
            destination_id = location_aliases[destination]
        else:
            raise RuntimeError(
                "Gameobject does not have a LocationAliases component. Destination cannot be a string."
            )
    else:
        destination_id = destination

    # A location cant move to itself
    if destination_id == gameobject.id:
        return

    # Update old location if needed
    if current_location_comp := gameobject.try_component(CurrentLocation):
        # Have to check if the location still has a location component
        # in-case te previous location is a closed business or demolished
        # building
        if current_location := world.try_gameobject(current_location_comp.location):
            if current_location.has_component(Location):
                current_location.get_component(Location).remove_entity(gameobject.id)

        gameobject.remove_component(CurrentLocation)

    # Move to new location if needed
    if destination_id is not None:
        location = world.get_gameobject(destination_id).get_component(Location)
        location.add_entity(gameobject.id)
        gameobject.add_component(CurrentLocation(destination_id))


def set_residence(
    world: World,
    character: GameObject,
    new_residence: Optional[GameObject],
    is_owner: bool = False,
) -> None:
    """
    Moves a character into a new permanent residence
    """

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = world.get_gameobject(resident.residence).get_component(
            Residence
        )

        if former_residence.is_owner(character.id):
            former_residence.remove_owner(character.id)

        former_residence.remove_resident(character.id)
        character.remove_component(Resident)

        if len(former_residence.residents) <= 0:
            former_residence.gameobject.add_component(Vacant())

        if location_aliases := character.try_component(LocationAliases):
            del location_aliases["home"]

    if new_residence is None:
        return

    # Move into new residence
    new_residence.get_component(Residence).add_resident(character.id)

    if is_owner:
        new_residence.get_component(Residence).add_owner(character.id)

    if not character.has_component(LocationAliases):
        character.add_component(LocationAliases())

    character.get_component(LocationAliases)["home"] = new_residence.id
    character.add_component(Resident(new_residence.id))

    if new_residence.has_component(Vacant):
        new_residence.remove_component(Vacant)


def depart_town(world: World, character: GameObject, reason: str = "") -> None:
    """
    Helper function that handles all the core logistics of moving someone
    out of the town
    """

    residence = world.get_gameobject(
        character.get_component(Resident).residence
    ).get_component(Residence)

    set_residence(world, character, None)
    departing_characters: List[GameObject] = [character]

    # Get people that this character lives with and have them depart with their
    # spouse(s) and children. This function may need to be refactored in the future
    # to perform BFS on the relationship tree when moving out extended families living
    # within the same residence
    for resident_id in residence.residents:
        resident = world.get_gameobject(resident_id)

        if resident == character:
            continue

        if character.get_component(Relationships).get(resident_id).has_tag("Spouse"):
            set_residence(world, resident, None)
            departing_characters.append(resident)

        elif character.get_component(Relationships).get(resident_id).has_tag("Child"):
            set_residence(world, resident, None)
            departing_characters.append(resident)

    world.get_resource(EventLog).record_event(
        DepartEvent(
            date=world.get_resource(SimDateTime),
            characters=departing_characters,
            reason=reason,
        )
    )


def check_share_residence(gameobject: GameObject, other: GameObject) -> bool:
    resident_comp = gameobject.try_component(Resident)
    other_resident_comp = other.try_component(Resident)

    return (
        resident_comp is not None
        and other_resident_comp is not None
        and resident_comp.residence == other_resident_comp.residence
    )


def demolish_building(world: World, gameobject: GameObject) -> None:
    """Remove the building component and free the land grid space"""
    settlement = world.get_resource(Settlement)
    settlement.land_map.free_lot(gameobject.get_component(Building).lot)
    gameobject.remove_component(Building)
    gameobject.remove_component(Position2D)


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


def choose_random_character_archetype(
    engine: NeighborlyEngine,
) -> Optional[ICharacterArchetype]:
    """Performs a weighted random selection across all character archetypes"""
    archetype_choices: List[ICharacterArchetype] = []
    archetype_weights: List[int] = []

    for archetype in engine.character_archetypes.get_all():
        archetype_choices.append(archetype)
        archetype_weights.append(archetype.get_spawn_frequency())

    if archetype_choices:
        # Choose an archetype at random
        archetype: ICharacterArchetype = engine.rng.choices(
            population=archetype_choices, weights=archetype_weights, k=1
        )[0]

        return archetype
    else:
        return None


def generate_child(
    world: World, parent_a: GameObject, parent_b: GameObject
) -> GameObject:
    child = BaseCharacterArchetype().create(world)

    required_components, random_pool = get_inheritable_traits_given_parents(
        parent_a, parent_b
    )

    for component_type in required_components:
        component = cast(IInheritable, component_type).from_parents(
            parent_a.try_component(component_type),
            parent_b.try_component(component_type),
        )
        child.add_component(component)

    rng = world.get_resource(NeighborlyEngine).rng

    rng.shuffle(random_pool)

    remaining_traits = 3

    for probability, component_type in random_pool:
        if rng.random() < probability:
            child.add_component(
                cast(IInheritable, component_type).from_parents(
                    parent_a.try_component(component_type),
                    parent_b.try_component(component_type),
                )
            )
            remaining_traits -= 1

        if remaining_traits <= 0:
            break

    return child


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

    if character.has_component(Unemployed):
        character.remove_component(Unemployed)

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
