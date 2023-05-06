import json
import math
import random
from typing import Any, Dict, Iterable, List, Optional, Tuple, TypeVar, Union

from neighborly.components.activity import Activities
from neighborly.components.business import (
    BossOf,
    Business,
    BusinessOwner,
    ClosedForBusiness,
    CoworkerOf,
    EmployeeOf,
    Occupation,
    OpenForBusiness,
    Services,
    Unemployed,
    WorkHistory,
)
from neighborly.components.character import (
    AgingConfig,
    Departed,
    GameCharacter,
    Gender,
    GenderType,
    LifeStage,
    LifeStageType,
    Married,
    ParentOf,
    ReproductionConfig,
)
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.shared import (
    Age,
    CurrentLocation,
    CurrentLot,
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
    Location,
    LocationAliases,
    Name,
    Position2D,
    PrefabName,
)
from neighborly.core.ecs import Active, GameObject, GameObjectFactory, World
from neighborly.core.life_event import AllEvents
from neighborly.core.location_bias import LocationBiasRules
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
    NewBusinessEvent,
    NewCharacterEvent,
    NewResidenceEvent,
    NewSettlementEvent,
    StartJobEvent,
)


def set_location(
    gameobject: GameObject, destination: Optional[Union[int, str]]
) -> None:
    world = gameobject.world

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
    if destination_id == gameobject.uid:
        return

    # Update old location if needed
    if current_location_comp := gameobject.try_component(CurrentLocation):
        # Have to check if the location still has a location component
        # in-case te previous location is a closed business or demolished
        # building
        if world.has_gameobject(current_location_comp.location):
            current_location = world.get_gameobject(current_location_comp.location)
            if current_location.has_component(Location):
                current_location.get_component(Location).remove_entity(gameobject.uid)

        gameobject.remove_component(CurrentLocation)

    # Move to new location if needed
    if destination_id is not None:
        location = world.get_gameobject(destination_id).get_component(Location)
        location.add_entity(gameobject.uid)
        gameobject.add_component(CurrentLocation(destination_id))


def spawn_settlement(
    world: World, prefab: str = "settlement", name: str = ""
) -> GameObject:
    """Create a new grid-based Settlement GameObject and add it to the world

    Parameters
    ----------
    world
        The world instance to add the settlement to
    prefab
        The name of the prefab with settlement data
    name
        Override name for the town

    Returns
    -------
    GameObject
        The newly created Settlement GameObject
    """
    settlement = GameObjectFactory.instantiate(world, prefab)

    if name:
        settlement.get_component(Name).value = name

    settlement.name = settlement.get_component(Name).value

    new_settlement_event = NewSettlementEvent(
        date=world.get_resource(SimDateTime), settlement=settlement
    )

    settlement.fire_event(new_settlement_event)

    return settlement


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
    location.add_component(Active())
    location.add_component(CurrentSettlement(settlement.uid))
    settlement.get_component(Settlement).locations.add(location.uid)


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

    settlement: GameObject = world.get_gameobject(
        location.get_component(CurrentSettlement).settlement
    )

    settlement.get_component(Settlement).locations.remove(location.uid)

    location.remove_component(CurrentSettlement)

    location.remove_component(Active)

    if frequented_by := settlement.try_component(FrequentedBy):
        for character_id in frequented_by:
            character = world.get_gameobject(character_id)
            if frequented_locations := character.try_component(FrequentedLocations):
                frequented_locations.remove(location.uid)

        frequented_by.clear()


def spawn_character(
    world: World,
    prefab: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    age: Optional[int] = None,
    life_stage: Optional[LifeStageType] = None,
    gender: Optional[GenderType] = None,
) -> GameObject:
    """Create a new GameCharacter GameObject and add it to the world

    Parameters
    ----------
    world
        The world instance to add the character to
    prefab
        The name of the prefab to instantiate
    first_name
        first name override (defaults to None)
    last_name
        last name override (defaults to None)
    age
        age override (defaults to None)
    life_stage
        life stage override (defaults to None)
    gender
        gender override (defaults to None)

    Returns
    -------
    GameObject
        The newly constructed character
    """

    character = GameObjectFactory.instantiate(world, prefab)

    set_character_age(
        character,
        _generate_age_from_life_stage(
            world.get_resource(random.Random),
            character.get_component(AgingConfig),
            LifeStageType.YoungAdult,
        ),
    )

    if first_name:
        set_character_name(character, first_name=first_name)

    if last_name:
        set_character_name(character, last_name=last_name)

    if age:
        set_character_age(character, age)

    if life_stage:
        set_character_life_stage(character, life_stage)

    if gender:
        character.get_component(Gender).gender = gender

    character.name = (
        f"{character.get_component(GameCharacter).full_name}({character.uid})"
    )

    new_character_event = NewCharacterEvent(
        date=world.get_resource(SimDateTime), character=character
    )

    character.fire_event(new_character_event)

    character.add_component(PrefabName(prefab))

    return character


def add_character_to_settlement(character: GameObject, settlement: GameObject) -> None:
    """Adds a character to a settlement

    Parameters
    ----------
    character
        The character to add
    settlement
        The settlement to add the character to
    """

    character.add_component(CurrentSettlement(settlement.uid))

    character.add_component(Active())

    set_frequented_locations(character, settlement)

    join_settlement_event = JoinSettlementEvent(
        character.world.get_resource(SimDateTime), settlement, character
    )

    character.fire_event(join_settlement_event)

    character.world.get_resource(AllEvents).append(join_settlement_event)


def remove_character_from_settlement(character: GameObject) -> None:
    """Remove a character from their settlement

    Parameters
    ----------
    character
        The character to add
    """

    world = character.world

    settlement = world.get_gameobject(
        character.get_component(CurrentSettlement).settlement
    )

    clear_frequented_locations(character)

    character.remove_component(Active)

    leave_settlement_event = LeaveSettlementEvent(
        character.world.get_resource(SimDateTime), settlement, character
    )

    character.fire_event(leave_settlement_event)

    character.world.get_resource(AllEvents).append(leave_settlement_event)


def spawn_residence(
    world: World,
    prefab: str,
) -> GameObject:
    """Instantiate a residence prefab

    Parameters
    ----------
    world
        The world instance to spawn the residence into
    prefab
        The name of a prefab to instantiate

    Returns
    -------
    GameObject
        The residence instance
    """
    residence = GameObjectFactory.instantiate(world, prefab)

    residence.fire_event(
        NewResidenceEvent(date=world.get_resource(SimDateTime), residence=residence)
    )

    residence.add_component(PrefabName(prefab))

    residence.name = f"{prefab}({residence.uid})"

    return residence


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
    settlement_comp.land_map.reserve_lot(lot_id, residence.uid)

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

    matching_prefabs = GameObjectFactory.get_matching_prefabs(*eligible_child_prefabs)

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

    world = character.world

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = world.get_gameobject(resident.residence)
        former_residence_comp = former_residence.get_component(Residence)

        if former_residence_comp.is_owner(character.uid):
            former_residence_comp.remove_owner(character.uid)

        former_residence_comp.remove_resident(character.uid)
        remove_status(character, Resident)

        former_settlement = world.get_gameobject(
            former_residence.get_component(CurrentSettlement).settlement
        ).get_component(Settlement)

        former_settlement.population -= 1

        if len(former_residence_comp.residents) <= 0:
            add_status(former_residence, Vacant())

    if new_residence is None:
        return

    # Move into new residence
    new_residence.get_component(Residence).add_resident(character.uid)

    new_settlement = world.get_gameobject(
        new_residence.get_component(CurrentSettlement).settlement
    )

    if is_owner:
        new_residence.get_component(Residence).add_owner(character.uid)

    add_status(
        character,
        Resident(new_residence.uid),
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


def depart_settlement(character: GameObject, reason: str = "") -> None:
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
        residence = world.get_gameobject(
            character.get_component(Resident).residence
        ).get_component(Residence)

        # Get people that this character lives with and have them depart with their
        # spouse(s) and children. This function may need to be refactored in the future
        # to perform BFS on the relationship tree when moving out extended families living
        # within the same residence
        for resident_id in residence.residents:
            resident = world.get_gameobject(resident_id)

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

        character.fire_event(depart_event)

    world.get_resource(AllEvents).append(depart_event)


#######################################
# Character Management
#######################################


def _generate_age_from_life_stage(
    rng: random.Random, aging_config: AgingConfig, life_stage_type: LifeStageType
) -> int:
    """Return an age for the character given their life_stage"""
    if life_stage_type == LifeStageType.Child:
        return rng.randint(0, aging_config.adolescent_age - 1)
    elif life_stage_type == LifeStageType.Adolescent:
        return rng.randint(
            aging_config.adolescent_age,
            aging_config.young_adult_age - 1,
        )
    elif life_stage_type == LifeStageType.YoungAdult:
        return rng.randint(
            aging_config.young_adult_age,
            aging_config.adult_age - 1,
        )
    elif life_stage_type == LifeStageType.Adult:
        return rng.randint(
            aging_config.adult_age,
            aging_config.senior_age - 1,
        )
    else:
        return aging_config.senior_age + int(10 * rng.random())


def set_character_age(character: GameObject, new_age: float) -> None:
    """Sets the name of a business"""
    age = character.get_component(Age)
    age.value = new_age

    if not character.has_component(AgingConfig):
        raise Exception(
            "Cannot set life stage for a character without an AgingConfig component"
        )

    aging_config = character.get_component(AgingConfig)

    life_stage = character.get_component(LifeStage)

    if age.value >= aging_config.senior_age:
        life_stage.life_stage = LifeStageType.Senior

    elif age.value >= aging_config.adult_age:
        life_stage.life_stage = LifeStageType.Adult

    elif age.value >= aging_config.young_adult_age:
        life_stage.life_stage = LifeStageType.YoungAdult

    elif age.value >= aging_config.adolescent_age:
        life_stage.life_stage = LifeStageType.Adolescent

    else:
        life_stage.life_stage = LifeStageType.Child


def set_character_life_stage(
    character: GameObject, life_stage_type: LifeStageType
) -> None:
    """Sets the name of a business"""
    age = character.get_component(Age)

    if not character.has_component(AgingConfig):
        raise Exception(
            "Cannot set life stage for a character without an AgingConfig component"
        )

    aging_config = character.get_component(AgingConfig)

    character.get_component(LifeStage).life_stage = life_stage_type

    if life_stage_type == LifeStageType.Senior:
        age.value = aging_config.senior_age

    elif life_stage_type == LifeStageType.Adult:
        age.value = aging_config.adult_age

    elif life_stage_type == LifeStageType.YoungAdult:
        age.value = aging_config.young_adult_age

    elif life_stage_type == LifeStageType.Adolescent:
        age.value = aging_config.adolescent_age

    elif life_stage_type == LifeStageType.Child:
        age.value = 0


def set_character_name(
    character: GameObject, first_name: str = "", last_name: str = ""
) -> None:
    """Sets the name of a business"""
    game_character = character.get_component(GameCharacter)

    if first_name:
        game_character.first_name = first_name

    if last_name:
        game_character.last_name = last_name

    character.name = f"{game_character.full_name}({character.uid})"


#######################################
# Business Management
#######################################


def set_business_name(business: GameObject, name: str) -> None:
    """Sets the name of a business"""
    business.name = name
    business.get_component(Name).value = name


def spawn_business(
    world: World,
    prefab: str,
    name: str = "",
) -> GameObject:
    business = GameObjectFactory.instantiate(world, prefab)

    if name:
        business.get_component(Name).value = name

    business.name = f"{business.get_component(Name).value}({business.uid})"

    business.add_component(PrefabName(prefab))

    new_business_event = NewBusinessEvent(
        date=world.get_resource(SimDateTime), business=business
    )

    business.fire_event(new_business_event)

    return business


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
    settlement_comp.businesses.add(business.uid)

    # Reserve the space
    settlement_comp.land_map.reserve_lot(lot_id, business.uid)

    # Set the position of the building
    lot_position = settlement_comp.land_map.get_lot_position(lot_id)
    business.add_component(Position2D(lot_position[0], lot_position[1]))

    # Give the business a building
    business.add_component(CurrentLot(lot_id))
    business.add_component(CurrentSettlement(settlement.uid))

    # Mark the business as an active GameObject
    business.add_component(Active())
    add_status(business, OpenForBusiness())

    # Set the current settlement
    business.add_component(CurrentSettlement(settlement.uid))

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
    settlement_obj = business.world.get_gameobject(current_settlement.settlement)
    settlement = settlement_obj.get_component(Settlement)

    event = BusinessClosedEvent(date, business)

    # Update the business as no longer active
    remove_status(business, OpenForBusiness)
    add_status(business, ClosedForBusiness())

    # Remove all the employees
    for employee in business_comp.get_employees():
        end_job(world.get_gameobject(employee), reason=event.get_type())

    # Remove the owner if applicable
    if business_comp.owner is not None:
        end_job(world.get_gameobject(business_comp.owner), reason=event.get_type())

    # Decrement the number of this type
    settlement.business_counts[prefab_ref.prefab] -= 1
    settlement.businesses.remove(business.uid)

    remove_location_from_settlement(business)

    # Demolish the building
    settlement.land_map.free_lot(current_lot.lot)
    business.remove_component(Position2D)
    # business.remove_component(CurrentSettlement)
    business.remove_component(CurrentLot)

    # Un-mark the business as active so it doesn't appear in queries
    business.remove_component(Location)

    business.fire_event(event)
    world.get_resource(AllEvents).append(event)


def end_job(
    character: GameObject,
    reason: str = "",
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
    business = world.get_gameobject(occupation.business)
    business_comp = business.get_component(Business)

    character.get_component(FrequentedLocations).locations.remove(business.uid)
    business.get_component(FrequentedBy).remove(character.uid)

    if character.has_component(BusinessOwner):
        remove_status(character, BusinessOwner)
        business_comp.set_owner(None)

        # Update relationships boss/employee relationships
        for employee_id in business.get_component(Business).get_employees():
            employee = world.get_gameobject(employee_id)

            remove_relationship_status(character, employee, BossOf)
            remove_relationship_status(employee, character, EmployeeOf)

            get_relationship(character, employee).get_component(
                InteractionScore
            ).increment(-1)
            get_relationship(employee, character).get_component(
                InteractionScore
            ).increment(-1)

    else:
        business_comp.remove_employee(character.uid)

        # Update boss/employee relationships if needed
        if business_comp.owner is not None:
            owner = world.get_gameobject(business_comp.owner)
            remove_relationship_status(owner, character, BossOf)
            remove_relationship_status(character, owner, EmployeeOf)

            get_relationship(character, owner).get_component(
                InteractionScore
            ).increment(-1)
            get_relationship(owner, character).get_component(
                InteractionScore
            ).increment(-1)

        # Update coworker relationships
        for employee_id in business.get_component(Business).get_employees():
            employee = world.get_gameobject(employee_id)

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
        business=business.uid,
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

    character.fire_event(end_job_event)

    # Emit the event
    world.get_resource(AllEvents).append(end_job_event)


def start_job(
    character: GameObject,
    business: GameObject,
    occupation_name: str,
    is_owner: bool = False,
) -> None:
    """Start the given character's job at the business.

    Parameters
    ----------
    character
        The character starting the job.
    business
        The business they will start working at.
    occupation_name
        The job title for their new occupation.
    is_owner
        Is this character going to be the owner of the
        business (defaults to False).
    """
    world = character.world
    business_comp = business.get_component(Business)
    occupation = Occupation(
        occupation_name, business.uid, world.get_resource(SimDateTime)
    )

    if character.has_component(Occupation):
        # Character must quit the old job before taking a new one
        raise RuntimeError("Cannot start a new job with existing Occupation component.")

    character.add_component(occupation)

    character.get_component(FrequentedLocations).locations.add(business.uid)
    business.get_component(FrequentedBy).add(character.uid)

    if has_status(character, Unemployed):
        remove_status(character, Unemployed)

    if is_owner:
        if business_comp.owner is not None:
            # The old owner needs to be removed before setting a new one
            raise RuntimeError("Owner is already set. Please end job first.")

        business_comp.set_owner(character.uid)
        add_status(character, BusinessOwner(business=business.uid))

        for employee_id in business.get_component(Business).get_employees():
            employee = world.get_gameobject(employee_id)
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
            owner = world.get_gameobject(business_comp.owner)
            add_relationship_status(owner, character, BossOf())
            add_relationship_status(character, owner, EmployeeOf())

            get_relationship(character, owner).get_component(
                InteractionScore
            ).increment(1)
            get_relationship(owner, character).get_component(
                InteractionScore
            ).increment(1)

        # Update employee/employee relationships
        for employee_id in business.get_component(Business).get_employees():
            employee = world.get_gameobject(employee_id)
            add_relationship_status(character, employee, CoworkerOf())
            add_relationship_status(employee, character, CoworkerOf())

            get_relationship(character, employee).get_component(
                InteractionScore
            ).increment(1)
            get_relationship(employee, character).get_component(
                InteractionScore
            ).increment(1)

        business_comp.add_employee(character.uid, occupation.occupation_type)

    start_job_event = StartJobEvent(
        character.world.get_resource(SimDateTime),
        business=business,
        character=character,
        occupation=occupation.occupation_type,
    )

    character.fire_event(start_job_event)
    character.world.get_resource(AllEvents).append(start_job_event)


def get_places_with_services(world: World, *services: str) -> List[int]:
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
    matches: List[int] = []
    for gid, services_component in world.get_component(Services):
        if all([s in services_component for s in services]):
            matches.append(gid)
    return matches


#######################################
# Activities and Location Frequenting
#######################################


def get_places_with_activities(
    world: World, settlement: GameObject, *activities: str
) -> List[int]:
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
    List[int]
         Returns the identifiers of locations
    """

    matches: List[int] = []

    settlement_comp = settlement.get_component(Settlement)

    for location_id in settlement_comp.locations:
        location_activities = world.get_gameobject(location_id).get_component(
            Activities
        )
        if all([a in location_activities for a in activities]):
            matches.append(location_id)

    return matches


def get_places_with_any_activities(
    world: World, settlement: GameObject, *activities: str
) -> List[int]:
    """
    Find businesses within the given settlement with any of the given activities

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
    List[int]
         Returns the identifiers of locations
    """

    def score_loc(act_list: Iterable[str]) -> int:
        location_score: int = 0
        for activity in activities:
            if activity in act_list:
                location_score += 1
        return location_score

    matches: List[Tuple[int, int]] = []

    settlement_comp = settlement.get_component(Settlement)

    for location_id in settlement_comp.locations:
        score = score_loc(world.get_gameobject(location_id).get_component(Activities))
        if score > 0:
            matches.append((score, location_id))

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
    return all([a in activities_comp for a in activities])


def _score_location(character: GameObject, location: GameObject) -> int:
    score: int = 0

    for rule_info in LocationBiasRules.iter_rules():
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

    for loc_id in selected_locations:
        character.get_component(FrequentedLocations).locations.add(loc_id)
        character.world.get_gameobject(loc_id).get_component(FrequentedBy).add(
            character.uid
        )


def clear_frequented_locations(character: GameObject) -> None:
    """
    Un-mark any locations as frequented by the given character

    Parameters
    ----------
    character
        The GameObject to remove as a frequenter
    """
    world = character.world
    frequented_locations = character.get_component(FrequentedLocations)

    for location_id in frequented_locations.locations:
        frequented_by_comp = world.get_gameobject(location_id).get_component(
            FrequentedBy
        )
        frequented_by_comp.remove(character.uid)

    frequented_locations.locations.clear()


#######################################
# General Utility Functions
#######################################

_KT = TypeVar("_KT")


def deep_merge(source: Dict[_KT, Any], other: Dict[_KT, Any]) -> Dict[_KT, Any]:
    """
    Merges two dictionaries (including any nested dictionaries) by overwriting
    fields in the source with the fields present in the other

    Parameters
    ----------
    source
        Dictionary with initial field values

    other
        Dictionary with fields to override in the source dict

    Returns
    -------
    Dict[_KT, Any]
        New dictionary with fields in source overwritten
        with values from the other
    """
    merged_dict = {**source}

    for key, value in other.items():
        if isinstance(value, dict):
            # get node or create one
            node = merged_dict.get(key, {})
            merged_dict[key] = deep_merge(node, value)  # type: ignore
        else:
            merged_dict[key] = value

    return merged_dict


def pprint_gameobject(gameobject: GameObject) -> None:
    """Pretty prints a GameObject"""
    print(
        json.dumps(
            gameobject.to_dict(),
            sort_keys=True,
            indent=2,
        )
    )
