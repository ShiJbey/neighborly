"""Helper functions for character operations.

"""

from __future__ import annotations

from typing import Optional, cast

from neighborly.components.business import Business, Occupation
from neighborly.components.character import Character
from neighborly.components.relationship import Relationship
from neighborly.components.residence import Resident, ResidentialUnit, Vacant
from neighborly.components.settlement import District
from neighborly.defs.base_types import CharacterDef, CharacterGenOptions, SpeciesDef
from neighborly.ecs import GameObject, World
from neighborly.events.defaults import DeathEvent
from neighborly.helpers.business import close_business, leave_job
from neighborly.helpers.location import (
    add_frequented_location,
    remove_all_frequented_locations,
    remove_frequented_location,
)
from neighborly.helpers.relationship import deactivate_relationships, get_relationship
from neighborly.helpers.traits import (
    add_trait,
    get_relationships_with_traits,
    has_trait,
    remove_trait,
)
from neighborly.libraries import CharacterLibrary, TraitLibrary
from neighborly.life_event import add_to_personal_history, dispatch_life_event


def create_character(
    world: World, definition_id: str, options: Optional[CharacterGenOptions] = None
) -> GameObject:
    """Create a new character instance.

    Parameters
    ----------
    world
        The simulation's World instance.
    definition_id
        The ID of the definition to instantiate.
    options
        Generation parameters.

    Returns
    -------
    GameObject
        An instantiated character.
    """
    character_library = world.resource_manager.get_resource(CharacterLibrary)

    character_def = character_library.get_definition(definition_id)

    options = options if options else CharacterGenOptions()

    character = character_def.instantiate(world, options)

    return character


def set_species(gameobject: GameObject, species_id: str) -> bool:
    """the species of the character.

    Parameters
    ----------
    gameobject
        The gameobject to add the trait to.
    species
        The ID of the species.

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """
    world = gameobject.world

    character = gameobject.get_component(Character)

    if character.species:
        remove_trait(gameobject, character.species.definition_id)

    if add_trait(gameobject, species_id):
        library = world.resources.get_resource(TraitLibrary)
        character.species = cast(SpeciesDef, library.get_definition(species_id))
        return True

    return False


def die(character: GameObject) -> None:
    """Have a character die."""

    death_event = DeathEvent(character)

    add_to_personal_history(character, death_event)
    dispatch_life_event(character.world, death_event)

    character.deactivate()

    remove_all_frequented_locations(character)

    add_trait(character, "deceased")

    deactivate_relationships(character)

    move_out_of_residence(character)

    # Remove the character from their residence
    if resident_data := character.try_component(Resident):
        residence = resident_data.residence
        move_out_of_residence(character)

        # If there are no-more residents that are owner's remove everyone from
        # the residence and have them depart the simulation.
        residence_data = residence.get_component(ResidentialUnit)
        if len(list(residence_data.owners)) == 0:
            residents = list(residence_data.residents)
            for resident in residents:
                depart_settlement(resident)

    # Adjust relationships
    for rel in get_relationships_with_traits(character, "dating"):
        target = rel.get_component(Relationship).target

        remove_trait(rel, "dating")
        remove_trait(get_relationship(target, character), "dating")

        add_trait(rel, "ex_partner")
        add_trait(get_relationship(target, character), "ex_partner")

    for rel in get_relationships_with_traits(character, "spouse"):
        target = rel.get_component(Relationship).target

        remove_trait(rel, "spouse")
        remove_trait(get_relationship(target, character), "spouse")

        add_trait(rel, "ex_spouse")
        add_trait(get_relationship(target, character), "ex_spouse")

        add_trait(rel, "widow")

    # Remove the character from their occupation
    if occupation := character.try_component(Occupation):
        leave_job(occupation.business, character)


def move_out_of_residence(character: GameObject) -> None:
    """Have the character move out of their current residence."""

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = resident.residence
        former_residence_comp = former_residence.get_component(ResidentialUnit)

        for resident in former_residence_comp.residents:
            if resident == character:
                continue

            remove_trait(get_relationship(character, resident), "live_together")
            remove_trait(get_relationship(resident, character), "live_together")

        if former_residence_comp.is_owner(character):
            former_residence_comp.remove_owner(character)

        former_residence_comp.remove_resident(character)
        character.remove_component(Resident)

        remove_frequented_location(character, former_residence)

        former_district = former_residence.get_component(
            ResidentialUnit
        ).district.get_component(District)
        former_district.population -= 1

        if len(former_residence_comp) <= 0:
            former_residence.add_component(Vacant(former_residence))


def move_into_residence(
    character: GameObject, new_residence: GameObject, is_owner: bool = False
) -> None:
    """Have the character move into a new residence."""

    new_residence.get_component(ResidentialUnit).add_resident(character)

    if is_owner:
        new_residence.get_component(ResidentialUnit).add_owner(character)

    character.add_component(Resident(character, residence=new_residence))

    add_frequented_location(character, new_residence)

    if new_residence.has_component(Vacant):
        new_residence.remove_component(Vacant)

    for resident in new_residence.get_component(ResidentialUnit).residents:
        if resident == character:
            continue

        add_trait(get_relationship(character, resident), "live_together")
        add_trait(get_relationship(resident, character), "live_together")

    new_district = new_residence.get_component(ResidentialUnit).district.get_component(
        District
    )
    new_district.population += 1


def depart_settlement(character: GameObject) -> None:
    """Have the given character depart the settlement."""

    remove_all_frequented_locations(character)
    add_trait(character, "departed")
    character.deactivate()

    deactivate_relationships(character)

    # Have the character leave their job
    if occupation := character.try_component(Occupation):
        if occupation.business.get_component(Business).owner == character:
            close_business(occupation.business)
        else:
            leave_job(occupation.business, character)

    # Have the character leave their residence
    if resident_data := character.try_component(Resident):
        residence_data = resident_data.residence.get_component(ResidentialUnit)
        move_out_of_residence(character)

        # Get people that this character lives with and have them depart with their
        # spouse(s) and children. This function may need to be refactored in the future
        # to perform BFS on the relationship tree when moving out extended families
        # living within the same residence
        for resident in list(residence_data.residents):
            if resident == character:
                continue

            rel_to_resident = get_relationship(character, resident)

            if has_trait(rel_to_resident, "spouse") and not has_trait(
                resident, "departed"
            ):
                depart_settlement(resident)

            elif has_trait(rel_to_resident, "child") and not has_trait(
                resident, "departed"
            ):
                depart_settlement(resident)


def register_character_def(world: World, definition: CharacterDef) -> None:
    """Add a new character definition for the CharacterLibrary.

    Parameters
    ----------
    world
        The world instance containing the character library.
    definition
        The definition to add.
    """
    world.resource_manager.get_resource(CharacterLibrary).add_definition(definition)
    world.resource_manager.get_resource(CharacterLibrary).add_definition(definition)
