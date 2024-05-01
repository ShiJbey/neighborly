"""Helper functions for character operations.

"""

from __future__ import annotations

import random

from neighborly.components.business import Business, Occupation
from neighborly.components.character import Character, LifeStage
from neighborly.components.relationship import Relationship
from neighborly.components.residence import (
    Resident,
    ResidentialBuilding,
    ResidentialUnit,
    Vacant,
)
from neighborly.components.settlement import District
from neighborly.components.shared import Age
from neighborly.components.stats import Lifespan
from neighborly.defs.base_types import CharacterDef
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
    add_relationship_trait,
    add_trait,
    get_relationships_with_traits,
    has_trait,
    remove_relationship_trait,
)
from neighborly.libraries import CharacterLibrary, TraitLibrary
from neighborly.life_event import add_to_personal_history, dispatch_life_event


def create_character(world: World, definition_id: str) -> GameObject:
    """Create a new character instance.

    Parameters
    ----------
    world
        The simulation's World instance.
    definition_id
        The ID of the definition to instantiate.

    Returns
    -------
    GameObject
        An instantiated character.
    """
    character_library = world.resource_manager.get_resource(CharacterLibrary)

    character_def = character_library.get_definition(definition_id)

    character = world.gameobject_manager.spawn_gameobject(
        components=character_def.components
    )
    character.metadata["definition_id"] = definition_id

    # Initialize the life span
    species = character.get_component(Character).species
    rng = character.world.resource_manager.get_resource(random.Random)
    min_value, max_value = (int(x.strip()) for x in species.lifespan.split("-"))
    base_lifespan = rng.randint(min_value, max_value)
    character.get_component(Lifespan).stat.base_value = base_lifespan

    _initialize_traits(character, character_def)

    return character


# def set_species(gameobject: GameObject, species: SpeciesDef) -> bool:
#     """the species of the character.

#     Parameters
#     ----------
#     gameobject
#         The gameobject to add the trait to.
#     species
#         The species.

#     Return
#     ------
#     bool
#         True if the trait was added successfully, False if already present or
#         if the trait conflict with existing traits.
#     """
#     world = gameobject.world

#     character = gameobject.get_component(Character)

#     if character.species:
#         remove_trait(gameobject, character.species.definition_id)

#     if add_trait(gameobject, species_id):
#         library = world.resources.get_resource(TraitLibrary)
#         character.species = cast(SpeciesDef, library.get_definition(species_id))
#         return True

#     return False


def set_rand_age(character: GameObject, life_stage: LifeStage) -> None:
    """Initializes the characters age."""
    rng = character.world.resource_manager.get_resource(random.Random)

    character_comp = character.get_component(Character)
    age = character.get_component(Age)
    species = character.get_component(Character).species

    character_comp.life_stage = life_stage

    # Generate an age for this character
    if life_stage == LifeStage.CHILD:
        age.value = rng.randint(0, species.adolescent_age - 1)
    elif life_stage == LifeStage.ADOLESCENT:
        age.value = rng.randint(
            species.adolescent_age,
            species.young_adult_age - 1,
        )
    elif life_stage == LifeStage.YOUNG_ADULT:
        age.value = rng.randint(
            species.young_adult_age,
            species.adult_age - 1,
        )
    elif life_stage == LifeStage.ADULT:
        age.value = rng.randint(
            species.adult_age,
            species.senior_age - 1,
        )
    else:
        age.value = species.senior_age


def _initialize_traits(character: GameObject, definition: CharacterDef) -> None:
    """Set the traits for a character."""
    rng = character.world.resource_manager.get_resource(random.Random)
    trait_library = character.world.resource_manager.get_resource(TraitLibrary)

    # species = character.get_component(Character).species

    # set_species(character, species.definition_id)

    # Loop through the trait entries in the definition and get by ID or select
    # randomly if using tags
    for entry in definition.traits:
        if entry.with_id:
            add_trait(character, entry.with_id)
        elif entry.with_tags:
            potential_traits = trait_library.get_definition_with_tags(entry.with_tags)

            traits: list[str] = []
            trait_weights: list[int] = []

            for trait_def in potential_traits:
                if trait_def.spawn_frequency >= 1:
                    traits.append(trait_def.definition_id)
                    trait_weights.append(trait_def.spawn_frequency)

            if len(traits) == 0:
                continue

            chosen_trait = rng.choices(population=traits, weights=trait_weights, k=1)[0]

            add_trait(character, chosen_trait)


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

        remove_relationship_trait(target, character, "dating")
        remove_relationship_trait(character, target, "dating")
        add_relationship_trait(target, character, "ex_partner")
        add_relationship_trait(character, target, "ex_partner")

    for rel in get_relationships_with_traits(character, "spouse"):
        target = rel.get_component(Relationship).target

        remove_relationship_trait(character, target, "spouse")
        remove_relationship_trait(target, character, "spouse")
        add_relationship_trait(target, character, "ex_spouse")
        add_relationship_trait(character, target, "ex_spouse")
        add_relationship_trait(target, character, "widow")

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

            add_relationship_trait(character, resident, "live_together")
            add_relationship_trait(resident, character, "live_together")

        if former_residence_comp.is_owner(character):
            former_residence_comp.remove_owner(character)

        former_residence_comp.remove_resident(character)
        character.remove_component(Resident)

        remove_frequented_location(character, former_residence)

        former_district = (
            former_residence.get_component(ResidentialUnit)
            .building.get_component(ResidentialBuilding)
            .district
        )

        if former_district:
            former_district.get_component(District).population -= 1

        if len(former_residence_comp) <= 0:
            former_residence.add_component(Vacant(former_residence))


def move_into_residence(
    character: GameObject, new_residence: GameObject, is_owner: bool = False
) -> None:
    """Have the character move into a new residence."""

    if character.has_component(Resident):
        move_out_of_residence(character)

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

        add_relationship_trait(character, resident, "live_together")
        add_relationship_trait(resident, character, "live_together")

    new_district = (
        new_residence.get_component(ResidentialUnit)
        .building.get_component(ResidentialBuilding)
        .district
    )

    if new_district:
        new_district.get_component(District).population += 1
    else:
        raise RuntimeError("Residential building is missing district.")


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
