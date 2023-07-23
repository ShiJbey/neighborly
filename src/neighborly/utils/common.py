from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple, Type

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
    Departed,
    GameCharacter,
    Gender,
    LifeStage,
    LifeStageType,
    Married,
    ParentOf,
)
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.role import Roles, add_role, remove_role
from neighborly.components.shared import (
    Age,
    CurrentLot,
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
    Location,
    Name,
    Position2D,
    PrefabName,
)
from neighborly.components.species import AgingConfig, Species
from neighborly.core.ecs import Active, GameObject, World
from neighborly.core.life_event import LifeEvent
from neighborly.core.location_preference import LocationPreferenceRuleLibrary
from neighborly.core.relationship import (
    InteractionScore,
    add_relationship_status,
    get_relationship,
    has_relationship_status,
    remove_relationship_status,
)
from neighborly.core.settlement import Settlement
from neighborly.core.status import add_status, clear_statuses, has_status, remove_status
from neighborly.core.time import SimDateTime
from neighborly.events import (
    BusinessClosedEvent,
    CharacterCreatedEvent,
    CharacterNameChangeEvent,
    DepartEvent,
    EndJobEvent,
    JoinSettlementEvent,
    LeaveSettlementEvent,
    NewBusinessEvent,
    ResidenceCreatedEvent,
    SettlementCreatedEvent,
    StartJobEvent,
)
from neighborly.utils.location import (
    add_frequented_location,
    add_sub_location,
    remove_frequented_location,
    remove_sub_location,
)

########################################
# SETTLEMENT MANAGEMENT
########################################


def spawn_settlement(
    world: World,
    name: str = "#settlement_name#",
    settlement_size: Tuple[int, int] = (5, 5),
) -> GameObject:
    width, length = settlement_size

    settlement = world.gameobject_manager.spawn_gameobject(
        components=[
            world.gameobject_manager.create_component(Name, value=name),
            world.gameobject_manager.create_component(
                Settlement, length=length, width=width
            ),
            world.gameobject_manager.create_component(Location),
            world.gameobject_manager.create_component(Age),
        ]
    )

    settlement.name = settlement.get_component(Name).value

    SettlementCreatedEvent(
        world=world,
        date=world.resource_manager.get_resource(SimDateTime).copy(),
        settlement=settlement,
    ).dispatch()

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
    location.add_component(CurrentSettlement(settlement))
    add_sub_location(settlement, location)


def remove_location_from_settlement(
    settlement: GameObject,
    location: GameObject,
) -> None:
    """Remove a location from a settlement.

    Parameters
    ----------
    settlement
        The settlement to remove the location from.
    location
        The location to remove.
    """
    location.remove_component(CurrentSettlement)

    # Remove this location from peoples frequented locations
    if frequented_by := settlement.try_component(FrequentedBy):
        for character in [*frequented_by]:
            remove_frequented_location(character, location)

    remove_sub_location(settlement, location)


def set_character_settlement(
    character: GameObject, settlement: Optional[GameObject]
) -> None:
    """Set the current settlement for a character.

    Parameters
    ----------
    character
        The character to modify
    settlement
        The settlement to assign them to. If None, the character is removed from their existing
        settlement and not reassigned to a new one.
    """

    if current_settlement := character.try_component(CurrentSettlement):
        current_settlement.settlement.get_component(Settlement).population -= 1

        event = LeaveSettlementEvent(
            character.world,
            character.world.resource_manager.get_resource(SimDateTime),
            current_settlement.settlement,
            character,
        )

        event.dispatch()

        character.remove_component(CurrentSettlement)

    if settlement is not None:
        settlement.get_component(Settlement).population += 1
        character.add_component(CurrentSettlement(settlement))

        JoinSettlementEvent(
            character.world,
            character.world.resource_manager.get_resource(SimDateTime),
            settlement,
            character,
        ).dispatch()


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
    rng = world.resource_manager.get_resource(random.Random)

    eligible_child_prefabs = [
        *parent_a.get_component(ReproductionConfig).child_prefabs,
    ]

    if parent_b:
        eligible_child_prefabs.extend(
            parent_a.get_component(ReproductionConfig).child_prefabs
        )

    matching_prefabs = world.gameobject_manager.get_matching_prefabs(
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
    current_date = character.world.resource_manager.get_resource(SimDateTime)

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
            add_status(former_residence, Vacant(year_created=current_date.year))

    if new_residence is None:
        return

    # Move into new residence
    new_residence.get_component(Residence).add_resident(character)

    new_settlement = new_residence.get_component(CurrentSettlement).settlement

    if is_owner:
        new_residence.get_component(Residence).add_owner(character)

    add_status(
        character,
        Resident(residence=new_residence, year_created=current_date.year),
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
    current_date = world.resource_manager.get_resource(SimDateTime)

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
        world=world,
        date=world.resource_manager.get_resource(SimDateTime),
        characters=departing_characters,
        reason=reason,
        settlement=character.get_component(CurrentSettlement).settlement,
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

        set_character_settlement(character, None)

        clear_frequented_locations(character)
        clear_statuses(character)
        character.deactivate()

        add_status(character, Departed(year_created=current_date.year))

        character.world.event_manager.dispatch_event(depart_event)


#######################################
# Character Management
#######################################


def spawn_character(
    world: World,
    prefab: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    age: Optional[int] = None,
    life_stage: Optional[LifeStageType] = None,
    gender: Optional[str] = None,
) -> GameObject:
    character = world.gameobject_manager.instantiate_prefab(prefab)

    if first_name:
        set_character_name(character, first_name=first_name)

    if last_name:
        set_character_name(character, last_name=last_name)

    if life_stage is not None:
        set_life_stage(character=character, life_stage_type=life_stage)

    if age is not None:
        set_character_age(character=character, new_age=age)

    if gender is not None:
        character.get_component(Gender).gender = gender

    character.name = (
        f"{character.get_component(GameCharacter).full_name}({character.uid})"
    )

    character.add_component(PrefabName(prefab))

    CharacterCreatedEvent(
        world=world,
        date=world.resource_manager.get_resource(SimDateTime),
        character=character,
    ).dispatch()

    return character


def set_character_name(
    character: GameObject, first_name: str = "", last_name: str = ""
) -> None:
    """Overwrite a characters first or last name.

    Parameters
    ----------
    character
        The character to modify
    first_name
        An optional override for the first name
    last_name
        An optional override for the last name
    """
    game_character = character.get_component(GameCharacter)

    if first_name:
        game_character.first_name = first_name

    if last_name:
        game_character.last_name = last_name

    # self.character.get_component(Name).value = game_character.full_name

    character.name = f"{game_character.full_name}({character.uid})"

    CharacterNameChangeEvent(
        character.world,
        character.world.resource_manager.get_resource(SimDateTime).copy(),
        character,
        game_character.first_name,
        game_character.last_name,
    ).dispatch()


def set_character_age(
    character: GameObject,
    new_age: int,
) -> None:
    age = character.get_component(Age)
    age.value = new_age

    species_type = character.get_component(Species).species_type

    if species_type.aging_config is None:
        return

    if character.has_component(LifeStage) is False:
        character.add_component(LifeStage("Adult"))

    life_stage = character.get_component(LifeStage)

    if age.value >= species_type.aging_config.senior_age:
        life_stage.life_stage = LifeStageType.Senior

    elif age.value >= species_type.aging_config.adult_age:
        life_stage.life_stage = LifeStageType.Adult

    elif age.value >= species_type.aging_config.young_adult_age:
        life_stage.life_stage = LifeStageType.YoungAdult

    elif age.value >= species_type.aging_config.adolescent_age:
        life_stage.life_stage = LifeStageType.Adolescent

    else:
        life_stage.life_stage = LifeStageType.Child


def set_life_stage(character: GameObject, life_stage_type: LifeStageType) -> None:
    """Overwrites the current LifeStage and age of a character.

    Parameters
    ----------
    character
        The character to modify
    life_stage_type
        The life stage to update to
    """
    age = character.get_component(Age)

    species_type = character.get_component(Species).species_type

    if species_type.aging_config is None:
        raise Exception(
            "Cannot set life stage for a species without an aging config"
        )

    character.get_component(LifeStage).life_stage = life_stage_type

    if life_stage_type == LifeStageType.Senior:
        age.value = species_type.aging_config.senior_age

    elif life_stage_type == LifeStageType.Adult:
        age.value = species_type.aging_config.adult_age

    elif life_stage_type == LifeStageType.YoungAdult:
        age.value = species_type.aging_config.young_adult_age

    elif life_stage_type == LifeStageType.Adolescent:
        age.value = species_type.aging_config.adolescent_age

    elif life_stage_type == LifeStageType.Child:
        age.value = 0


def generate_age_from_life_stage(
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


#######################################
# Business Management
#######################################


def spawn_business(world: World, prefab_name: str, name: str = "") -> GameObject:
    business = world.gameobject_manager.instantiate_prefab(prefab_name)

    if name:
        business.get_component(Name).value = name

    business.name = f"{business.get_component(Name).value}({business.uid})"

    business.add_component(PrefabName(prefab_name))

    NewBusinessEvent(
        world=world,
        business=business,
    ).dispatch()

    return business


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
    current_date = business.world.resource_manager.get_resource(SimDateTime)

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
    add_status(business, OpenForBusiness(year_created=current_date.year))

    # Set the current settlement
    business.add_component(CurrentSettlement(settlement))

    # Add the business as a location within the town if it has a location component
    if business.has_component(Location):
        add_location_to_settlement(business, settlement)


def shutdown_business(business: GameObject) -> None:
    """Close a business and remove all employees and the owner.

    Parameters
    ----------
    business
        Business to shut down.
    """
    world = business.world
    current_date = world.resource_manager.get_resource(SimDateTime)
    business_comp = business.get_component(Business)
    prefab_ref = business.get_component(PrefabName)
    current_settlement = business.get_component(CurrentSettlement)
    current_lot = business.get_component(CurrentLot)
    settlement_obj = current_settlement.settlement
    settlement = settlement_obj.get_component(Settlement)

    event = BusinessClosedEvent(world, current_date, business)

    event.dispatch()

    # Update the business as no longer active
    remove_status(business, OpenForBusiness)
    add_status(business, ClosedForBusiness(year_created=current_date.year))

    # Remove all the employees
    for employee, _ in [*business_comp.iter_employees()]:
        end_job(employee, business, reason=event)

    # Remove the owner if applicable
    if business_comp.owner is not None:
        end_job(business_comp.owner, business, reason=event)

    # Decrement the number of this type
    settlement.business_counts[prefab_ref.prefab] -= 1
    settlement.businesses.remove(business)

    remove_location_from_settlement(
        location=business, settlement=current_settlement.settlement
    )

    # Demolish the building
    settlement.land_map.free_lot(current_lot.lot)
    business.remove_component(Position2D)
    # business.remove_component(CurrentSettlement)
    business.remove_component(CurrentLot)

    # Un-mark the business as active so it doesn't appear in queries
    business.remove_component(Location)
    business.deactivate()
    world.event_manager.dispatch_event(event)


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
        remove_status(business_comp.owner, BusinessOwner)
        business_comp.set_owner(None)

        # Update relationships boss/employee relationships
        for employee, _ in business.get_component(Business).iter_employees():
            remove_relationship_status(character, employee, BossOf)
            remove_relationship_status(employee, character, EmployeeOf)

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
            remove_relationship_status(owner, character, BossOf)
            remove_relationship_status(character, owner, EmployeeOf)

            get_relationship(character, owner).get_component(
                InteractionScore
            ).base_value += -1
            get_relationship(owner, character).get_component(
                InteractionScore
            ).base_value += -1

        # Update coworker relationships
        for employee, _ in business.get_component(Business).iter_employees():
            remove_relationship_status(character, employee, CoworkerOf)
            remove_relationship_status(employee, character, CoworkerOf)

            get_relationship(character, employee).get_component(
                InteractionScore
            ).base_value += -1
            get_relationship(employee, character).get_component(
                InteractionScore
            ).base_value += -1

    add_status(character, Unemployed(year_created=current_date.year))

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

    remove_role(character, occupation_type)


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

    occupation = world.gameobject_manager.create_component(
        occupation_type, business=business, start_year=current_date.year
    )

    add_role(character, occupation)

    add_frequented_location(character, business)

    if has_status(character, Unemployed):
        remove_status(character, Unemployed)

    if is_owner:
        if business_comp.owner is not None:
            # The old owner needs to be removed before setting a new one
            raise RuntimeError("Owner is already set. Please end job first.")

        business_comp.set_owner(character)
        add_status(
            character, BusinessOwner(business=business, year_created=current_date.year)
        )

        for employee, _ in business.get_component(Business).iter_employees():
            add_relationship_status(
                character, employee, BossOf(year_created=current_date.year)
            )
            add_relationship_status(
                employee, character, EmployeeOf(year_created=current_date.year)
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

            add_relationship_status(
                owner, character, BossOf(year_created=current_date.year)
            )
            add_relationship_status(
                character, owner, EmployeeOf(year_created=current_date.year)
            )

            get_relationship(character, owner).get_component(
                InteractionScore
            ).base_value += 1
            get_relationship(owner, character).get_component(
                InteractionScore
            ).base_value += 1

        # Update employee/employee relationships
        for employee, _ in business.get_component(Business).iter_employees():
            add_relationship_status(
                character, employee, CoworkerOf(year_created=current_date.year)
            )
            add_relationship_status(
                employee, character, CoworkerOf(year_created=current_date.year)
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


def get_places_with_services(world: World, *services: str) -> List[GameObject]:
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
        if all([s in services_component for s in services]):
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
# Residence Management
#######################################


def spawn_residence(world: World, prefab_name: str) -> GameObject:
    """Spawn a new residence into the world."""

    residence = world.gameobject_manager.instantiate_prefab(prefab_name)

    ResidenceCreatedEvent(
        world=world,
        timestamp=world.resource_manager.get_resource(SimDateTime),
        residence=residence,
    )

    residence.add_component(PrefabName(prefab_name))

    residence.name = f"{prefab_name}({residence.uid})"

    return residence


#######################################
# Services and Location Frequenting
#######################################


def location_has_services(location: GameObject, *services: str) -> bool:
    """Check if the location has the given services

    Parameters
    ----------
    location
        The location to check.
    *services
        Service names.

    Returns
    -------
    bool
        True if all the services are offered by the location, False otherwise.
    """
    services_comp = location.get_component(Services)
    return all([entry in services_comp for entry in services])


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


def score_frequentable_locations(
    character: GameObject, settlement: GameObject
) -> List[Tuple[float, GameObject]]:
    """Score the frequentable locations in a settlement and return.

    Parameters
    ----------
    character
        The character to score the location in reference to
    settlement
        The settlement to search within

    Returns
    -------
    List[Tuple[float, GameObject]]
        A list of tuples containing location scores and the location, sorted in descending order
    """

    locations = [
        character.world.gameobject_manager.get_gameobject(guid)
        for guid, (_, current_settlement, _, _) in character.world.get_components(
            (Location, CurrentSettlement, Services, Active)
        )
        if current_settlement.settlement == settlement
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
        A value between start and end that is a fractional amount between the two points.
    """
    return (start * (1.0 - f)) + (end * f)
