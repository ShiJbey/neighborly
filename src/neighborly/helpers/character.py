"""Helper functions for character operations.

"""

from __future__ import annotations

import random

from neighborly.components.character import Character, LifeStage, Species
from neighborly.components.shared import Age
from neighborly.ecs import Event, GameObject, World
from neighborly.libraries import CharacterLibrary


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

    return character_library.factory.create_character(world, definition_id)


def create_child(birthing_parent: GameObject, other_parent: GameObject) -> GameObject:
    """Create instance of a child from two parents.

    Parameters
    ----------
    birthing_parent
        The parent who gave birth to the child.
    other_parent
        The other parent contributing genetics to the child.

    Returns
    -------
    GameObject
        The new child.
    """
    character_library = birthing_parent.world.resource_manager.get_resource(
        CharacterLibrary
    )

    return character_library.child_factory.create_child(birthing_parent, other_parent)


def set_character_name(
    character: Character, *, first_name: str = "", last_name: str = ""
) -> None:
    """Set a character's first or last name."""

    if first_name:
        character.first_name = first_name

    if last_name:
        character.last_name = last_name

    character.gameobject.name = character.full_name

    character.gameobject.dispatch_event(
        Event(
            "name-changed",
            world=character.gameobject.world,
            character=character,
            name=character.full_name,
        )
    )


def set_random_character_age(character: Character, life_stage: LifeStage) -> None:
    """Set's the character to the given life stage and generates a valid age."""

    rng = character.gameobject.world.resources.get_resource(random.Random)
    species = character.gameobject.get_component(Species).species

    if life_stage == LifeStage.SENIOR:
        age = rng.randint(species.senior_age, species.lifespan[1])
    elif life_stage == LifeStage.ADULT:
        age = rng.randint(species.adult_age, species.senior_age - 1)
    elif life_stage == LifeStage.YOUNG_ADULT:
        age = rng.randint(species.young_adult_age, species.adult_age - 1)
    elif life_stage == LifeStage.ADOLESCENT:
        age = rng.randint(species.adolescent_age, species.young_adult_age - 1)
    else:
        age = rng.randint(0, species.adolescent_age - 1)

    character.life_stage = life_stage
    character.gameobject.get_component(Age).value = float(age)


def set_character_age(character: Character, age: int) -> None:
    """Set a character's age."""

    character.gameobject.get_component(Age).value = float(age)
    species = character.gameobject.get_component(Species).species
    character.life_stage = species.get_life_stage_for_age(age)
