import math
import random
from typing import Iterable, List, Optional, Tuple

from neighborly.components.activity import Activities, ActivityLibrary
from neighborly.components.business import (
    BossOf,
    Business,
    BusinessOwner,
    ClosedForBusiness,
    CoworkerOf,
    EmployeeOf,
    Occupation,
    OpenForBusiness,
    ServiceLibrary,
    Services,
    Unemployed,
    WorkHistory,
)
from neighborly.components.character import (
    Departed,
    Married,
    ParentOf,
    ReproductionConfig,
)
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.shared import (
    CurrentLocation,
    CurrentLot,
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
    Location,
    Name,
    Position2D,
    PrefabName,
)
from neighborly.core.ecs import Active, GameObject, GameObjectFactory, World
from neighborly.core.life_event import LifeEvent
from neighborly.core.location_bias import LocationBiasRuleLibrary
from neighborly.core.relationship import (
    InteractionScore,
    add_relationship_status,
    get_relationship,
    has_relationship_status,
    remove_relationship_status,
)
from neighborly.core.settlement import Settlement
from neighborly.core.status import add_status, clear_statuses, has_status, remove_status
from neighborly.core.time import DAYS_PER_YEAR, SimDateTime
from neighborly.events import (
    BusinessClosedEvent,
    DepartEvent,
    EndJobEvent,
    JoinSettlementEvent,
    LeaveSettlementEvent,
    StartJobEvent,
)

########################################
# LOCATION MANAGEMENT
########################################


def add_sub_location(parent_location: GameObject, sub_location: GameObject) -> None:
    """Adds a location as a child of another location.

    Parameters
    ----------
    parent_location
        The location to add a child to.
    sub_location
        The new location to add.
    """
    parent_location.get_component(Location).children.add(sub_location)
    sub_location.get_component(Location).parent = parent_location.uid
    parent_location.add_child(sub_location)


def set_location(gameobject: GameObject, location: Optional[GameObject]) -> None:
    """Move a GameObject to a location.

    Parameters
    ----------
    gameobject
        The object to move.
    location
        The location to move the object to.
    """

    # Update old location if needed
    if current_location_comp := gameobject.try_component(CurrentLocation):
        # Have to check if the location still has a location component
        # in-case te previous location is a closed business or demolished
        # building

        focus = current_location_comp.location

        while focus is not None:
            location_component = focus.get_component(Location)
            location_component.remove_entity(gameobject)

            if location_component.parent:
                focus = location_component.parent
            else:
                focus = None

        gameobject.remove_component(CurrentLocation)

    # Move to new location if needed
    if location is not None:
        gameobject.add_component(CurrentLocation(location))

        focus = location

        while focus is not None:
            location_component = focus.get_component(Location)
            location_component.add_entity(gameobject)

            if location_component.parent:
                focus = location_component.parent
            else:
                focus = None


def at_location(gameobject: GameObject, location: GameObject) -> bool:
    """Check if a GameObject is at a location.

    Parameters
    ----------
    gameobject
        The object to check.
    location
        The location to check for the GameObject.

    Returns
    -------
    bool
        True if the object is at the location, False otherwise.
    """
    return location.get_component(Location).has_entity(gameobject)


########################################
# SETTLEMENT MANAGEMENT
########################################


def add_location_to_settlement(
    location: GameObject,
    settlement: GameObject,
) -> None:
    """Add a location to a settlement

    Parameters
    ----------
    location
        The location to add
    settlement
        The settlement to add the location to
    """
    location.add_component(CurrentSettlement(settlement))
    add_sub_location(settlement, location)


def remove_location_from_settlement(
    location: GameObject,
) -> None:
    """Remove a location from a settlement

    Parameters
    ----------
    location
        The location to remove
    """
    world = location.world

    settlement: GameObject = location.get_component(CurrentSettlement).settlement

    location.remove_component(CurrentSettlement)

    location.deactivate()

    if frequented_by := settlement.try_component(FrequentedBy):
        for character_id in frequented_by:
            character = world.get_gameobject(character_id)
            if frequented_locations := character.try_component(FrequentedLocations):
                frequented_locations.remove(location)

        frequented_by.clear()


def add_character_to_settlement(character: GameObject, settlement: GameObject) -> None:
    """Adds a character to a settlement

    Parameters
    ----------
    character
        The character to add
    settlement
        The settlement to add the character to
    """

    character.add_component(CurrentSettlement(settlement))

    character.add_component(Active())

    set_frequented_locations(character, settlement)

    join_settlement_event = JoinSettlementEvent(
        character.world.get_resource(SimDateTime), settlement, character
    )

    character.world.fire_event(join_settlement_event)


def remove_character_from_settlement(character: GameObject) -> None:
    """Remove a character from their settlement

    Parameters
    ----------
    character
        The character to add
    """

    world = character.world

    settlement = character.get_component(CurrentSettlement).settlement

    clear_frequented_locations(character)

    character.remove_component(Active)

    leave_settlement_event = LeaveSettlementEvent(
        character.world.get_resource(SimDateTime), settlement, character
    )

    world.fire_event(leave_settlement_event)


def add_residence_to_settlement(
    residence: GameObject, settlement: GameObject, lot_id: Optional[int] = None
) -> None:
    """Add a residence GameObject to the given settlement

    Parameters
    ----------
    residence
        The residence to add
    settlement
        The settlement to add the residence to
    lot_id
        The ID of a lot to set the residence to
    """
    settlement_comp = settlement.get_component(Settlement)

    if lot_id is None:
        # If a lot is not supplied, get the first available lot
        # If none is available this will throw an IndexError which is
        # fine since we don't want this to succeed if there is nowhere
        # to build
        lot_id = settlement_comp.land_map.get_vacant_lots()[0]

    # Reserve the space
    settlement_comp.land_map.reserve_lot(lot_id, residence)

    # Set the position of the building
    position = settlement_comp.land_map.get_lot_position(lot_id)
    residence.add_component(Position2D(position[0], position[1]))

    residence.add_component(CurrentLot(lot_id))
    residence.add_component(Active())

    add_location_to_settlement(residence, settlement)


def get_child_prefab(
    parent_a: GameObject, parent_b: Optional[GameObject] = None
) -> Optional[str]:
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
    rng = world.get_resource(random.Random)

    eligible_child_prefabs = [
        *parent_a.get_component(ReproductionConfig).child_prefabs,
    ]

    if parent_b:
        eligible_child_prefabs.extend(
            parent_a.get_component(ReproductionConfig).child_prefabs
        )

    matching_prefabs = world.get_resource(GameObjectFactory).get_matching_prefabs(
        *eligible_child_prefabs
    )

    if matching_prefabs:
        return rng.choice(matching_prefabs).name

    return None


def set_residence(
    character: GameObject,
    new_residence: Optional[GameObject],
    is_owner: bool = False,
) -> None:
    """
    Moves a character into a new permanent residence
    """

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = resident.residence
        former_residence_comp = former_residence.get_component(Residence)

        if former_residence_comp.is_owner(character):
            former_residence_comp.remove_owner(character)

        former_residence_comp.remove_resident(character)
        remove_status(character, Resident)

        former_settlement = former_residence.get_component(
            CurrentSettlement
        ).settlement.get_component(Settlement)

        former_settlement.population -= 1

        if len(former_residence_comp.residents) <= 0:
            add_status(former_residence, Vacant())

    if new_residence is None:
        return

    # Move into new residence
    new_residence.get_component(Residence).add_resident(character)

    new_settlement = new_residence.get_component(CurrentSettlement).settlement

    if is_owner:
        new_residence.get_component(Residence).add_owner(character)

    add_status(
        character,
        Resident(new_residence),
    )

    if new_residence.has_component(Vacant):
        remove_status(new_residence, Vacant)

    new_settlement.get_component(Settlement).population += 1


def check_share_residence(gameobject: GameObject, other: GameObject) -> bool:
    """Check if two characters live in the same residence.

    Parameters
    ----------
    gameobject
        A character.
    other
        Another character.

    Returns
    -------
    bool
        True if the characters live together, False otherwise.
    """
    resident_comp = gameobject.try_component(Resident)
    other_resident_comp = other.try_component(Resident)

    return (
        resident_comp is not None
        and other_resident_comp is not None
        and resident_comp.residence == other_resident_comp.residence
    )


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

    departing_characters: List[GameObject] = [character]

    if character.has_component(Resident):
        residence = character.get_component(Resident).residence.get_component(Residence)

        # Get people that this character lives with and have them depart with their
        # spouse(s) and children. This function may need to be refactored in the future
        # to perform BFS on the relationship tree when moving out extended families living
        # within the same residence
        for resident in residence.residents:
            if resident == character:
                continue

            if has_relationship_status(character, resident, Married):
                departing_characters.append(resident)

            elif has_relationship_status(character, resident, ParentOf):
                departing_characters.append(resident)

    depart_event = DepartEvent(
        date=world.get_resource(SimDateTime),
        characters=departing_characters,
        reason=reason,
    )

    for character in departing_characters:
        if character.has_component(Occupation):
            end_job(character, reason=reason)

        if character.has_component(Resident):
            set_residence(character, None)

        remove_character_from_settlement(character)

        clear_frequented_locations(character)
        clear_statuses(character)

        add_status(character, Departed())

        character.world.fire_event(depart_event)


#######################################
# Business Management
#######################################


def set_business_name(business: GameObject, name: str) -> None:
    """Sets the name of a business"""
    business.name = name
    business.get_component(Name).value = name


def add_business_to_settlement(
    business: GameObject,
    settlement: GameObject,
    lot_id: Optional[int] = None,
) -> None:
    """Add a business gameobject to a settlement

    Parameters
    ----------
    business
        The business to add
    settlement
        The settlement to add the business to
    lot_id
        The lot to place the business on (defaults to None)
    """

    settlement_comp = settlement.get_component(Settlement)

    if lot_id is None:
        # If a lot is not supplied, get the first available lot
        # If none is available this will throw an IndexError which is
        # fine since we don't want this to succeed if there is nowhere
        # to build
        lot_id = settlement_comp.land_map.get_vacant_lots()[0]

    # Increase the count of this business type in the settlement
    settlement_comp.business_counts[business.get_component(PrefabName).prefab] += 1
    settlement_comp.businesses.add(business)

    # Reserve the space
    settlement_comp.land_map.reserve_lot(lot_id, business)

    # Set the position of the building
    lot_position = settlement_comp.land_map.get_lot_position(lot_id)
    business.add_component(Position2D(lot_position[0], lot_position[1]))

    # Give the business a building
    business.add_component(CurrentLot(lot_id))
    business.add_component(CurrentSettlement(settlement))

    # Mark the business as an active GameObject
    business.add_component(Active())
    add_status(business, OpenForBusiness())

    # Set the current settlement
    business.add_component(CurrentSettlement(settlement))

    # Add the business as a location within the town if it has a location component
    if business.has_component(Location):
        add_location_to_settlement(business, settlement)


def shutdown_business(business: GameObject) -> None:
    """Close a business and remove all employees and the owner

    This shuts down the business, but it does not remove it from the
    town map. That has to be done with the 'remove_business' function

    Parameters
    ----------
    business
        Business to shut down in the town
    """
    world = business.world
    date = world.get_resource(SimDateTime)
    business_comp = business.get_component(Business)
    prefab_ref = business.get_component(PrefabName)
    # building = business.get_component(Building)
    current_settlement = business.get_component(CurrentSettlement)
    current_lot = business.get_component(CurrentLot)
    settlement_obj = current_settlement.settlement
    settlement = settlement_obj.get_component(Settlement)

    event = BusinessClosedEvent(date, business)

    # Update the business as no longer active
    remove_status(business, OpenForBusiness)
    add_status(business, ClosedForBusiness())

    # Remove all the employees
    for employee in business_comp.get_employees():
        end_job(employee, reason=event)

    # Remove the owner if applicable
    if business_comp.owner is not None:
        end_job(business_comp.owner, reason=event)

    # Decrement the number of this type
    settlement.business_counts[prefab_ref.prefab] -= 1
    settlement.businesses.remove(business)

    remove_location_from_settlement(business)

    # Demolish the building
    settlement.land_map.free_lot(current_lot.lot)
    business.remove_component(Position2D)
    # business.remove_component(CurrentSettlement)
    business.remove_component(CurrentLot)

    # Un-mark the business as active so it doesn't appear in queries
    business.remove_component(Location)

    world.fire_event(event)


def end_job(
    character: GameObject,
    reason: Optional[LifeEvent] = None,
) -> None:
    """End a characters current occupation

    Parameters
    ----------
    character
        The characters whose job to terminate
    reason
        The reason for them leaving their job (defaults to "")
    """
    world = character.world
    occupation = character.get_component(Occupation)
    business = occupation.business
    business_comp = business.get_component(Business)

    character.get_component(FrequentedLocations).remove(business)
    business.get_component(FrequentedBy).remove(character)

    if character.has_component(BusinessOwner):
        remove_status(character, BusinessOwner)
        business_comp.set_owner(None)

        # Update relationships boss/employee relationships
        for employee in business.get_component(Business).get_employees():
            remove_relationship_status(character, employee, BossOf)
            remove_relationship_status(employee, character, EmployeeOf)

            get_relationship(character, employee).get_component(
                InteractionScore
            ).increment(-1)
            get_relationship(employee, character).get_component(
                InteractionScore
            ).increment(-1)

    else:
        business_comp.remove_employee(character)

        # Update boss/employee relationships if needed
        if business_comp.owner is not None:
            owner = business_comp.owner
            remove_relationship_status(owner, character, BossOf)
            remove_relationship_status(character, owner, EmployeeOf)

            get_relationship(character, owner).get_component(
                InteractionScore
            ).increment(-1)
            get_relationship(owner, character).get_component(
                InteractionScore
            ).increment(-1)

        # Update coworker relationships
        for employee in business.get_component(Business).get_employees():
            remove_relationship_status(character, employee, CoworkerOf)
            remove_relationship_status(employee, character, CoworkerOf)

            get_relationship(character, employee).get_component(
                InteractionScore
            ).increment(-1)
            get_relationship(employee, character).get_component(
                InteractionScore
            ).increment(-1)

    character.remove_component(Occupation)

    add_status(character, Unemployed())

    # Update the former employee's work history
    if not character.has_component(WorkHistory):
        character.add_component(WorkHistory())

    current_date = character.world.get_resource(SimDateTime)

    character.get_component(WorkHistory).add_entry(
        occupation_type=occupation.occupation_type,
        business=business,
        years_held=float((current_date - occupation.start_date).total_days)
        / DAYS_PER_YEAR,
        reason_for_leaving=reason,
    )

    end_job_event = EndJobEvent(
        date=world.get_resource(SimDateTime),
        character=character,
        business=business,
        occupation=occupation.occupation_type,
        reason=reason,
    )

    world.fire_event(end_job_event)


def start_job(
    character: GameObject,
    business: GameObject,
    occupation_type: GameObject,
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

    occupation = Occupation(occupation_type, business, world.get_resource(SimDateTime))

    if character.has_component(Occupation):
        # Character must quit the old job before taking a new one
        raise RuntimeError("Cannot start a new job with existing Occupation component.")

    character.add_component(occupation)

    character.get_component(FrequentedLocations).add(business)
    business.get_component(FrequentedBy).add(character)

    if has_status(character, Unemployed):
        remove_status(character, Unemployed)

    if is_owner:
        if business_comp.owner is not None:
            # The old owner needs to be removed before setting a new one
            raise RuntimeError("Owner is already set. Please end job first.")

        business_comp.set_owner(character)
        add_status(character, BusinessOwner(business=business))

        for employee in business.get_component(Business).get_employees():
            add_relationship_status(character, employee, BossOf())
            add_relationship_status(employee, character, EmployeeOf())

            get_relationship(character, employee).get_component(
                InteractionScore
            ).increment(1)
            get_relationship(employee, character).get_component(
                InteractionScore
            ).increment(1)

    else:
        # Update boss/employee relationships if needed
        if business_comp.owner is not None:
            add_relationship_status(business_comp.owner, character, BossOf())
            add_relationship_status(character, business_comp.owner, EmployeeOf())

            get_relationship(character, business_comp.owner).get_component(
                InteractionScore
            ).increment(1)
            get_relationship(business_comp.owner, character).get_component(
                InteractionScore
            ).increment(1)

        # Update employee/employee relationships
        for employee in business.get_component(Business).get_employees():
            add_relationship_status(character, employee, CoworkerOf())
            add_relationship_status(employee, character, CoworkerOf())

            get_relationship(character, employee).get_component(
                InteractionScore
            ).increment(1)
            get_relationship(employee, character).get_component(
                InteractionScore
            ).increment(1)

        business_comp.add_employee(character, occupation_type)

    start_job_event = StartJobEvent(
        character.world.get_resource(SimDateTime),
        business=business,
        character=character,
        occupation=occupation_type,
    )

    world.fire_event(start_job_event)


def get_places_with_services(world: World, *services: str) -> List[GameObject]:
    """
    Get all the active locations with the given services

    Parameters
    ----------
    world
        The world instance to search within

    services
        The services to search for

    Returns
    -------
    The IDs of the matching entities
    """
    matches: List[GameObject] = []
    service_library = world.get_resource(ServiceLibrary)
    service_objs = [service_library.get(s) for s in services]
    for gid, services_component in world.get_component(Services):
        if all([s in services_component for s in service_objs]):
            matches.append(world.get_gameobject(gid))
    return matches


#######################################
# Activities and Location Frequenting
#######################################


def get_places_with_activities(
    world: World, settlement: GameObject, *activities: str
) -> List[GameObject]:
    """
    Find businesses within the given settlement with all the given activities

    Parameters
    ----------
    world
        The World instance of the simulation
    settlement
        The settlement to search within
    *activities
        Activities to search for

    Returns
    -------
    List[GameObject]
         Returns the identifiers of locations
    """

    matches: List[GameObject] = []

    settlement_comp = settlement.get_component(Settlement)
    activity_library = world.get_resource(ActivityLibrary)
    activity_types = [activity_library.get(a) for a in activities]

    for location in settlement_comp.locations:
        location_activities = location.get_component(Activities)
        if all([a in location_activities for a in activity_types]):
            matches.append(location)

    return matches


def get_places_with_any_activities(
    settlement: GameObject, *activities: str
) -> List[GameObject]:
    """
    Find businesses within the given settlement with any of the given activities

    Parameters
    ----------
    settlement
        The settlement to search within
    *activities
        Activities to search for

    Returns
    -------
    List[GameObject]
         Returns the identifiers of locations
    """

    def score_loc(act_list: Iterable[str]) -> int:
        location_score: int = 0
        for activity in activities:
            if activity in act_list:
                location_score += 1
        return location_score

    matches: List[Tuple[int, GameObject]] = []

    settlement_comp = settlement.get_component(Settlement)

    for location in settlement_comp.locations:
        score = score_loc(location.get_component(Activities))
        if score > 0:
            matches.append((score, location))

    return [match[1] for match in sorted(matches, key=lambda m: m[0], reverse=True)]


def location_has_activities(location: GameObject, *activities: str) -> bool:
    """Check if the location has the given activities

    Parameters
    ----------
    location
        The location to check.
    *activities
        Activity names.

    Returns
    -------
    bool
        True if the activities are offered by the location, False otherwise.
    """
    activities_comp = location.get_component(Activities)
    activity_library = location.world.get_resource(ActivityLibrary)
    activity_types = [activity_library.get(a) for a in activities]
    return all([a in activities_comp for a in activity_types])


def _score_location(character: GameObject, location: GameObject) -> int:
    score: int = 0
    rule_library = character.world.get_resource(LocationBiasRuleLibrary)
    for rule_info in rule_library.iter_rules():
        if modifier := rule_info.rule(character, location):
            score += modifier

    return score


def calculate_location_probabilities(
    character: GameObject, locations: List[GameObject]
) -> List[Tuple[float, GameObject]]:
    """Calculate the probability distribution for a character and set of locations"""

    score_total: float = 0
    scores: List[Tuple[float, GameObject]] = []

    # Score each location
    for loc in locations:
        score = _score_location(character, loc)
        score_total += math.exp(score)
        scores.append((math.exp(score), loc))

    # Perform softmax
    probabilities = [(score / score_total, loc) for score, loc in scores]

    # Sort
    probabilities.sort(key=lambda pair: pair[0], reverse=True)

    return probabilities


def set_frequented_locations(
    character: GameObject, settlement: GameObject, max_locations: int = 3
) -> None:
    """
    Set what locations a character frequents based on the locations within
    a given settlement

    Parameters
    ----------
    character
        The character to set frequented locations for
    settlement
        The settlement to sample frequented locations from
    max_locations
        The max number of locations to sample
    """
    clear_frequented_locations(character)

    # For all locations available in the settlement
    locations = [
        character.world.get_gameobject(guid)
        for guid, (_, current_settlement, _, _) in character.world.get_components(
            (Location, CurrentSettlement, Activities, Active)
        )
        if current_settlement.settlement == settlement.uid
    ]

    scores = [_score_location(character, location) for location in locations]

    pairs = list(zip(locations, scores))

    pairs.sort(key=lambda pair: pair[1])

    selected_locations = [loc.uid for loc, _ in pairs[:max_locations]]

    for loc in selected_locations:
        character.get_component(FrequentedLocations).add(loc)
        loc.get_component(FrequentedBy).add(character)


def clear_frequented_locations(character: GameObject) -> None:
    """
    Un-mark any locations as frequented by the given character

    Parameters
    ----------
    character
        The GameObject to remove as a frequenter
    """
    frequented_locations = character.get_component(FrequentedLocations)

    for location in frequented_locations:
        frequented_by_comp = location.get_component(FrequentedBy)
        frequented_by_comp.remove(character)

    frequented_locations.clear()


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
