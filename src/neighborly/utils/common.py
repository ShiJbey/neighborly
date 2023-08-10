from __future__ import annotations

import random
from typing import List, Optional, Type

from neighborly.components.business import (
    BossOf,
    Business,
    BusinessClosedEvent,
    BusinessOwner,
    ClosedForBusiness,
    CoworkerOf,
    EmployeeOf,
    EndJobEvent,
    Occupation,
    OpenForBusiness,
    Services,
    ServiceType,
    StartJobEvent,
    Unemployed,
    WorkHistory,
)
from neighborly.components.character import (
    CharacterType,
    Deceased,
    Departed,
    GameCharacter,
    Married,
    ParentOf,
)
from neighborly.components.residence import Residence, Resident
from neighborly.components.shared import (
    FrequentedBy,
    FrequentedLocations,
    Location,
    Position2D,
)
from neighborly.ecs import Active, GameObject, World
from neighborly.events import DeathEvent, DepartEvent
from neighborly.life_event import LifeEvent
from neighborly.relationship import InteractionScore, Relationships
from neighborly.roles import Roles
from neighborly.spawn_table import BusinessSpawnTable
from neighborly.time import SimDateTime
from neighborly.world_map import BuildingMap

########################################
# CHARACTER MANAGEMENT
########################################


def get_random_child_character_type(
    parent_a: GameObject, parent_b: Optional[GameObject] = None
) -> Type[CharacterType]:
    """Returns a random prefab for a potential child

    This function chooses a random Prefab from the union of eligible child prefab names
    listed in each character's configuration.

    Parameters
    ----------
    parent_a
        Reference to one parent
    parent_b
        Reference to another parent if two parents are present

    Returns
    -------
    str or None
        The name of a prefab for a potential child
    """

    world = parent_a.world
    rng = world.resource_manager.get_resource(random.Random)

    eligible_child_prefabs: List[Type[CharacterType]] = [
        type(parent_a.get_component(GameCharacter).character_type)
    ]

    if parent_b:
        eligible_child_prefabs.append(
            type(parent_b.get_component(GameCharacter).character_type)
        )

    return rng.choice(eligible_child_prefabs)


def depart_settlement(
    character: GameObject, reason: Optional[LifeEvent] = None
) -> None:
    """
    Helper function that handles all the core logistics of moving someone
    out of the town

    This function will also cause any spouses or children that live with
    the given character to depart too.

    Parameters
    ----------
    character
        The character initiating the departure
    reason
        An optional reason for departing from the settlement
    """
    world = character.world
    current_date = world.resource_manager.get_resource(SimDateTime)

    departing_characters: List[GameObject] = [character]

    if character.has_component(Resident):
        residence = character.get_component(Resident).residence.get_component(Residence)

        # Get people that this character lives with and have them depart with their
        # spouse(s) and children. This function may need to be refactored in the future
        # to perform BFS on the relationship tree when moving out extended families
        # living within the same residence
        for resident in residence.residents:
            if resident == character:
                continue

            if (
                character.get_component(Relationships)
                .get_relationship(resident)
                .has_component(Married)
            ):
                departing_characters.append(resident)

            elif (
                character.get_component(Relationships)
                .get_relationship(resident)
                .has_component(ParentOf)
            ):
                departing_characters.append(resident)

    depart_event = DepartEvent(
        world=world,
        date=world.resource_manager.get_resource(SimDateTime),
        characters=departing_characters,
        reason=reason,
    )

    for character in departing_characters:
        for occupation in character.get_component(Roles).get_roles_of_type(Occupation):
            if occupation.business.get_component(Business).owner == character:
                shutdown_business(occupation.business)
            else:
                end_job(
                    character=character,
                    business=occupation.business,
                    reason=depart_event,
                )

        character.deactivate()

        character.add_component(Departed, timestamp=current_date.year)

    depart_event.dispatch()


def die(character: GameObject) -> None:
    """Run death procedures for a character."""

    current_date = character.world.resource_manager.get_resource(SimDateTime)

    event = DeathEvent(
        character.world,
        current_date,
        character,
    )

    for occupation in character.get_component(Roles).get_roles_of_type(Occupation):
        if occupation.business.get_component(Business).owner == character:
            shutdown_business(occupation.business)
        else:
            end_job(
                character=character,
                business=occupation.business,
                reason=event,
            )

    character.deactivate()

    character.add_component(Deceased, timestamp=current_date.year)

    event.dispatch()


#######################################
# BUSINESS MANAGEMENT
#######################################


def shutdown_business(business: GameObject) -> None:
    """Close a business and remove all employees and the owner.

    Parameters
    ----------
    business
        The business to shut down.
    """
    world = business.world
    current_date = world.resource_manager.get_resource(SimDateTime)
    building_map = world.resource_manager.get_resource(BuildingMap)
    business_comp = business.get_component(Business)
    building_position = business.get_component(Position2D)
    business_spawn_table = world.resource_manager.get_resource(BusinessSpawnTable)

    event = BusinessClosedEvent(world, current_date, business)

    event.dispatch()

    # Update the business as no longer active
    business.remove_component(OpenForBusiness)
    business.add_component(ClosedForBusiness, timestamp=current_date.year)

    # Remove all the employees
    for employee, _ in [*business_comp.iter_employees()]:
        end_job(employee, business, reason=event)

    # Remove the owner if applicable
    if business_comp.owner is not None:
        end_job(business_comp.owner, business, reason=event)

    # Decrement the number of this type
    business_spawn_table.decrement_count(type(business_comp.business_type).__name__)

    # Remove any other characters that frequent the location
    if frequented_by := business.try_component(FrequentedBy):
        frequented_by.clear()

    # Demolish the building
    building_map.remove_building_from_lot(building_position.as_tuple())
    business.remove_component(Position2D)

    # Un-mark the business as active so it doesn't appear in queries
    business.remove_component(Location)
    business.deactivate()


def end_job(
    character: GameObject,
    business: GameObject,
    reason: Optional[LifeEvent] = None,
) -> None:
    """End a characters current occupation.

    Parameters
    ----------
    character
        The character whose job to terminate.
    business
        The business where the character currently works.
    reason
        The reason for them leaving their job (defaults to None).
    """
    world = character.world
    current_date = world.resource_manager.get_resource(SimDateTime)
    business_comp = business.get_component(Business)

    character.get_component(FrequentedLocations).remove_location(business)

    if business_comp.owner and character == business_comp.owner:
        occupation_type = business_comp.owner_type
        business_comp.owner.remove_component(BusinessOwner)
        business_comp.set_owner(None)

        # Update relationships boss/employee relationships
        for employee, _ in business.get_component(Business).iter_employees():
            character.get_component(Relationships).get_relationship(
                employee
            ).remove_component(BossOf)
            employee.get_component(Relationships).get_relationship(
                character
            ).remove_component(EmployeeOf)

            character.get_component(Relationships).get_relationship(
                employee
            ).get_component(InteractionScore).base_value += -1
            employee.get_component(Relationships).get_relationship(
                character
            ).get_component(InteractionScore).base_value += -1

    else:
        occupation_type = business_comp.get_employee_role(character)
        business_comp.remove_employee(character)

        # Update boss/employee relationships if needed
        owner = business_comp.owner
        if owner is not None:
            owner.get_component(Relationships).get_relationship(
                character
            ).remove_component(BossOf)
            character.get_component(Relationships).get_relationship(
                owner
            ).remove_component(EmployeeOf)

            owner.get_component(Relationships).get_relationship(
                character
            ).get_component(InteractionScore).base_value += -1
            character.get_component(Relationships).get_relationship(
                owner
            ).get_component(InteractionScore).base_value += -1

        # Update coworker relationships
        for employee, _ in business.get_component(Business).iter_employees():
            character.get_component(Relationships).get_relationship(
                employee
            ).remove_component(CoworkerOf)
            employee.get_component(Relationships).get_relationship(
                character
            ).remove_component(CoworkerOf)

            character.get_component(Relationships).get_relationship(
                employee
            ).get_component(InteractionScore).base_value += -1
            employee.get_component(Relationships).get_relationship(
                character
            ).get_component(InteractionScore).base_value += -1

    character.add_component(Unemployed, timestamp=current_date.year)

    current_date = character.world.resource_manager.get_resource(SimDateTime)

    occupation = character.get_component(occupation_type)

    character.get_component(WorkHistory).add_entry(
        occupation_type=occupation_type,
        business=business,
        years_held=(current_date.year - occupation.start_year),
        reason_for_leaving=reason,
    )

    end_job_event = EndJobEvent(
        world=world,
        date=world.resource_manager.get_resource(SimDateTime),
        character=character,
        business=business,
        occupation=occupation_type,
        reason=reason,
    )

    world.event_manager.dispatch_event(end_job_event)

    character.remove_component(occupation_type)


def start_job(
    character: GameObject,
    business: GameObject,
    occupation_type: Type[Occupation],
    is_owner: bool = False,
) -> None:
    """Start the given character's job at the business.

    Parameters
    ----------
    character
        The character starting the job.
    business
        The business they will start working at.
    occupation_type
        The job title for their new occupation.
    is_owner
        Is this character going to be the owner of the
        business (defaults to False).
    """
    world = character.world
    business_comp = business.get_component(Business)
    current_date = world.resource_manager.get_resource(SimDateTime)

    character.add_component(
        occupation_type, business=business, start_year=current_date.year
    )

    character.get_component(FrequentedLocations).add_location(business)

    if character.has_component(Unemployed):
        character.remove_component(Unemployed)

    if is_owner:
        if business_comp.owner is not None:
            # The old owner needs to be removed before setting a new one
            raise RuntimeError("Owner is already set. Please end job first.")

        business_comp.set_owner(character)
        character.add_component(
            BusinessOwner, business=business, year_created=current_date.year
        )

        for employee, _ in business.get_component(Business).iter_employees():
            character.get_component(Relationships).get_relationship(
                employee
            ).add_component(BossOf, timestamp=current_date.year)

            employee.get_component(Relationships).get_relationship(
                character
            ).add_component(EmployeeOf, timestamp=current_date.year)

            character.get_component(Relationships).get_relationship(
                employee
            ).get_component(InteractionScore).base_value += 1

            employee.get_component(Relationships).get_relationship(
                character
            ).get_component(InteractionScore).base_value += 1

    else:
        # Update boss/employee relationships if needed
        if business_comp.owner is not None:
            owner = business_comp.owner

            owner.get_component(Relationships).get_relationship(
                character
            ).add_component(BossOf, timestamp=current_date.year)

            character.get_component(Relationships).get_relationship(
                owner
            ).add_component(EmployeeOf, timestamp=current_date.year)

            owner.get_component(Relationships).get_relationship(
                character
            ).get_component(InteractionScore).base_value += 1

            character.get_component(Relationships).get_relationship(
                owner
            ).get_component(InteractionScore).base_value += 1

        # Update employee/employee relationships
        for employee, _ in business.get_component(Business).iter_employees():
            character.get_component(Relationships).get_relationship(
                employee
            ).add_component(CoworkerOf, timestamp=current_date.year)

            employee.get_component(Relationships).get_relationship(
                character
            ).add_component(CoworkerOf, timestamp=current_date.year)

            character.get_component(Relationships).get_relationship(
                employee
            ).get_component(InteractionScore).base_value += 1

            employee.get_component(Relationships).get_relationship(
                character
            ).get_component(InteractionScore).base_value += 1

        business_comp.add_employee(character, occupation_type)

    start_job_event = StartJobEvent(
        world=character.world,
        date=character.world.resource_manager.get_resource(SimDateTime),
        business=business,
        character=character,
        occupation=occupation_type,
    )

    world.event_manager.dispatch_event(start_job_event)


def get_places_with_services(world: World, services: ServiceType) -> List[GameObject]:
    """Get all the active locations with the given services.

    Parameters
    ----------
    world
        The world instance to search within

    services
        The services to search for

    Returns
    -------
    List[GameObject]
        Businesses with the services
    """
    matches: List[GameObject] = []

    for gid, services_component, _ in world.get_components((Services, Active)):
        if services in services_component:
            matches.append(world.gameobject_manager.get_gameobject(gid))

    return matches


def is_employed(gameobject: GameObject) -> bool:
    """Check if a character has an occupation role.

    Parameters
    ----------
    gameobject
        The GameObject to check

    Returns
    -------
    bool
        True if the GameObject has a role with an Occupation component. False otherwise.
    """
    return len(gameobject.get_component(Roles).get_roles_of_type(Occupation)) > 0


#######################################
# GENERAL UTILITY
#######################################


def debug_print_gameobject(gameobject: GameObject) -> None:
    """Pretty prints a GameObject"""

    component_debug_strings = "".join(
        [f"\t{c.__repr__()}\n" for c in gameobject.get_components()]
    )

    debug_str = (
        f"name: {gameobject.name}\n"
        f"uid: {gameobject.uid}\n"
        f"components: [\n{component_debug_strings}]"
    )

    print(debug_str)


def lerp(start: float, end: float, f: float) -> float:
    """Linearly interpolate between start and end values.

    Parameters
    ----------
    start
        The starting value.
    end
        The ending value.
    f
        A fractional amount on the interval [0, 1.0].

    Returns
    -------
    float
        A value between start and end that is a fractional amount between the two
        points.
    """
    return (start * (1.0 - f)) + (end * f)
