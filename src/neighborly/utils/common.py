from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple, Type

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
    Departed,
    GameCharacter,
    Married,
    ParentOf,
)
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.shared import (
    FrequentedBy,
    FrequentedLocations,
    Location,
    Position2D,
)
from neighborly.core.ecs import Active, GameObject, World
from neighborly.core.life_event import LifeEvent
from neighborly.core.location_preference import LocationPreferenceRuleLibrary
from neighborly.core.relationship import InteractionScore, get_relationship
from neighborly.core.time import SimDateTime
from neighborly.events import ChangeResidenceEvent, DepartEvent
from neighborly.role_system import Roles
from neighborly.settlement import Settlement
from neighborly.spawn_table import BusinessSpawnTable
from neighborly.status_system import clear_statuses
from neighborly.utils.location import (
    add_frequented_location,
    remove_frequented_location,
)
from neighborly.world_map import BuildingMap

########################################
# SETTLEMENT MANAGEMENT
########################################


def get_child_prefab(
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


def set_residence(
    character: GameObject,
    new_residence: Optional[GameObject],
    is_owner: bool = False,
) -> None:
    """Sets the characters current residence.

    Parameters
    ----------
    character
        The character to move
    new_residence
        An optional residence to move them to. If None is given and the character
        has a current residence, they are removed from their current residence
    is_owner
        Should the character be listed one of the owners of the new residence
    """
    current_date = character.world.resource_manager.get_resource(SimDateTime)
    settlement = character.world.resource_manager.get_resource(Settlement)
    former_residence: Optional[GameObject] = None

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = resident.residence
        former_residence_comp = former_residence.get_component(Residence)

        if former_residence_comp.is_owner(character):
            former_residence_comp.remove_owner(character)

        former_residence_comp.remove_resident(character)
        character.remove_component(Resident)

        settlement.population -= 1

        if len(former_residence_comp.residents) <= 0:
            former_residence.add_component(Vacant, timestamp=current_date.year)

    # Don't add them to a new residence if none is given
    if new_residence is None:
        return

    # Move into new residence
    new_residence.get_component(Residence).add_resident(character)

    if is_owner:
        new_residence.get_component(Residence).add_owner(character)

    character.add_component(
        Resident, residence=new_residence, year_created=current_date.year
    )

    if new_residence.has_component(Vacant):
        new_residence.remove_component(Vacant)

    settlement.population += 1

    ChangeResidenceEvent(
        world=character.world,
        old_residence=former_residence,
        new_residence=new_residence,
        character=character,
        date=current_date.copy(),
    ).dispatch()


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

            if get_relationship(character, resident).has_component(Married):
                departing_characters.append(resident)

            elif get_relationship(character, resident).has_component(ParentOf):
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

        if character.has_component(Resident):
            set_residence(character, None)

        clear_frequented_locations(character)
        clear_statuses(character)
        character.deactivate()

        character.add_component(Departed, timestamp=current_date.year)

        character.world.event_manager.dispatch_event(depart_event)


#######################################
# Business Management
#######################################


def shutdown_business(business: GameObject) -> None:
    """Close a business and remove all employees and the owner.

    Parameters
    ----------
    business
        Business to shut down.
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
        for character in [*frequented_by]:
            remove_frequented_location(character, business)

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

    remove_frequented_location(character, business)

    if business_comp.owner and character == business_comp.owner:
        occupation_type = business_comp.owner_type
        business_comp.owner.remove_component(BusinessOwner)
        business_comp.set_owner(None)

        # Update relationships boss/employee relationships
        for employee, _ in business.get_component(Business).iter_employees():
            get_relationship(character, employee).remove_component(BossOf)
            get_relationship(employee, character).remove_component(EmployeeOf)

            get_relationship(character, employee).get_component(
                InteractionScore
            ).base_value += -1
            get_relationship(employee, character).get_component(
                InteractionScore
            ).base_value += -1

    else:
        occupation_type = business_comp.get_employee_role(character)
        business_comp.remove_employee(character)

        # Update boss/employee relationships if needed
        if business_comp.owner is not None:
            owner = business_comp.owner
            get_relationship(owner, character).remove_component(BossOf)
            get_relationship(character, owner).remove_component(EmployeeOf)

            get_relationship(character, owner).get_component(
                InteractionScore
            ).base_value += -1
            get_relationship(owner, character).get_component(
                InteractionScore
            ).base_value += -1

        # Update coworker relationships
        for employee, _ in business.get_component(Business).iter_employees():
            get_relationship(character, employee).remove_component(CoworkerOf)
            get_relationship(employee, character).remove_component(CoworkerOf)

            get_relationship(character, employee).get_component(
                InteractionScore
            ).base_value += -1
            get_relationship(employee, character).get_component(
                InteractionScore
            ).base_value += -1

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

    add_frequented_location(character, business)

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
            get_relationship(character, employee).add_component(
                BossOf, timestamp=current_date.year
            )

            get_relationship(employee, character).add_component(
                EmployeeOf, timestamp=current_date.year
            )

            get_relationship(character, employee).get_component(
                InteractionScore
            ).base_value += 1
            get_relationship(employee, character).get_component(
                InteractionScore
            ).base_value += 1

    else:
        # Update boss/employee relationships if needed
        if business_comp.owner is not None:
            owner = business_comp.owner

            get_relationship(owner, character).add_component(
                BossOf, timestamp=current_date.year
            )

            get_relationship(character, owner).add_component(
                EmployeeOf, timestamp=current_date.year
            )

            get_relationship(character, owner).get_component(
                InteractionScore
            ).base_value += 1
            get_relationship(owner, character).get_component(
                InteractionScore
            ).base_value += 1

        # Update employee/employee relationships
        for employee, _ in business.get_component(Business).iter_employees():
            get_relationship(character, employee).add_component(
                CoworkerOf, timestamp=current_date.year
            )
            get_relationship(employee, character).add_component(
                CoworkerOf, timestamp=current_date.year
            )

            get_relationship(character, employee).get_component(
                InteractionScore
            ).base_value += 1
            get_relationship(employee, character).get_component(
                InteractionScore
            ).base_value += 1

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

    for gid, services_component in world.get_component(Services):
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
# Services and Location Frequenting
#######################################


def location_has_services(location: GameObject, services: ServiceType) -> bool:
    """Check if the location has the given services

    Parameters
    ----------
    location
        The location to check.
    services
        Service types.

    Returns
    -------
    bool
        True if all the services are offered by the location, False otherwise.
    """
    services_comp = location.get_component(Services)
    return services in services_comp


def score_location(character: GameObject, location: GameObject) -> float:
    """Scores a location using location preference rules.

    Parameters
    ----------
    character
        The character to calculate scores for
    location
        The location to score

    Returns
    -------
    float
        The probability of wanting to frequent this location
    """

    cumulative_score: float = 1.0
    consideration_count: int = 0
    rule_library = character.world.resource_manager.get_resource(
        LocationPreferenceRuleLibrary
    )

    for rule_info in rule_library.iter_rules():
        consideration_score = rule_info.rule(character, location)
        if consideration_score is not None:
            assert 0.0 <= consideration_score
            cumulative_score *= consideration_score
            consideration_count += 1

        if cumulative_score == 0.0:
            break

    if consideration_count == 0:
        consideration_count = 1
        cumulative_score = 0.0

    # Scores are averaged using the Geometric Mean instead of
    # arithmetic mean. It calculates the mean of a product of
    # n-numbers by finding the n-th root of the product
    # Tried using the averaging scheme by Dave Mark, but it
    # returned values that felt too small and were not easy
    # to reason about.
    # Using this method, a cumulative score of zero will still
    # result in a final score of zero.

    final_score = cumulative_score ** (1 / consideration_count)

    return final_score


def calculate_location_probabilities(
    character: GameObject, locations: List[GameObject]
) -> List[Tuple[float, GameObject]]:
    """Calculate the probability distribution for a character and set of locations"""

    score_total: float = 0
    scores: List[Tuple[float, GameObject]] = []

    # Score each location
    for loc in locations:
        score = score_location(character, loc)
        score_total += math.exp(score)
        scores.append((math.exp(score), loc))

    # Perform softmax
    probabilities = [(score / score_total, loc) for score, loc in scores]

    # Sort
    probabilities.sort(key=lambda pair: pair[0], reverse=True)

    return probabilities


def score_locations_to_frequent(
    character: GameObject,
) -> List[Tuple[float, GameObject]]:
    """Score potential locations for the character to frequent.

    Parameters
    ----------
    character
        The character to score the location in reference to

    Returns
    -------
    List[Tuple[float, GameObject]]
        A list of tuples containing location scores and the location, sorted in
        descending order
    """

    locations = [
        character.world.gameobject_manager.get_gameobject(guid)
        for guid, (_, _, _) in character.world.get_components(
            (Location, Services, Active)
        )
    ]

    scores = calculate_location_probabilities(character, locations)

    return scores


def clear_frequented_locations(character: GameObject) -> None:
    """
    Un-mark any locations as frequented by the given character

    Parameters
    ----------
    character
        The GameObject to remove as a frequenter
    """
    frequented_locations = character.get_component(FrequentedLocations)

    for location in [*frequented_locations]:
        remove_frequented_location(character, location)


#######################################
# General Utility Functions
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
