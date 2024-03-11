"""Helper functions for character operations.

"""

from __future__ import annotations

from neighborly.ecs import GameObject, World
from neighborly.factories.character import CharacterFactory, CharacterGenerationOptions
from neighborly.libraries import CharacterLibrary


def create_character(world: World, options: CharacterGenerationOptions) -> GameObject:
    """Create a new character object.

    Parameters
    ----------
    world
        The world instance to spawn the character into.
    options
        Various creation settings.

    Returns
    -------
    GameObject
        The new character object.
    """

    character_def = world.resources.get_resource(CharacterLibrary).get_definition(
        options.definition_id
    )

    character = world.resources.get_resource(CharacterFactory).instantiate(
        world, character_def, options
    )

    return character


def register_character_def(world: World, definition: CharacterDef) -> None:
    """Add a new character definition for the CharacterLibrary.

    Parameters
    ----------
    world
        The world instance containing the character library.
    definition
        The definition to add.
    """
    world.resources.get_resource(CharacterLibrary).add_definition(definition)


def die(character: GameObject) -> None:
    """Have the character dies"""
    character = self.roles["subject"]
    remove_all_frequented_locations(character)
    character.deactivate()
    add_trait(character, "deceased")

    deactivate_relationships(character)

    # Remove the character from their residence
    if resident_data := character.try_component(Resident):
        residence = resident_data.residence
        ChangeResidenceEvent(subject=character, new_residence=None).dispatch()

        # If there are no-more residents that are owner's remove everyone from
        # the residence and have them depart the simulation.
        residence_data = residence.get_component(ResidentialUnit)
        if len(list(residence_data.owners)) == 0:
            residents = list(residence_data.residents)
            for resident in residents:
                DepartSettlement(resident, "death in family")

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
        LeaveJob(
            subject=character,
            business=occupation.business,
            job_role=occupation.job_role.gameobject,
            reason="died",
        ).dispatch()
