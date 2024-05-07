"""Character Component Factories.

"""

import random
from typing import Any

from neighborly.components.character import Character, Sex
from neighborly.components.shared import Age
from neighborly.components.stats import Lifespan
from neighborly.defs.base_types import CharacterDef
from neighborly.ecs import Component, ComponentFactory, GameObject, World
from neighborly.helpers.traits import add_trait
from neighborly.libraries import (
    CharacterLibrary,
    CharacterNameFactories,
    ICharacterFactory,
    IChildFactory,
    SpeciesLibrary,
    TraitLibrary,
)


class CharacterFactory(ComponentFactory):
    """Creates Character component instances."""

    __component__ = "Character"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        name_factories = world.resources.get_resource(CharacterNameFactories)

        first_name = ""
        if name := kwargs.get("first_name", ""):
            first_name = name
        elif name_factory := kwargs.get("first_name_factory", ""):
            name = name_factories.get_factory(name_factory)(world)

        last_name = ""
        if name := kwargs.get("last_name", ""):
            last_name = name
        elif name_factory := kwargs.get("last_name_factory", ""):
            name = name_factories.get_factory(name_factory)(world)

        species_id: str = kwargs["species"]
        sex: Sex = Sex[kwargs["sex"]]

        species_library = world.resources.get_resource(SpeciesLibrary)
        species = species_library.get_species(species_id)

        return Character(
            first_name=first_name,
            last_name=last_name,
            sex=sex,
            species=species,
        )


class DefaultCharacterFactory(ICharacterFactory):
    """Default implementation of a character factory."""

    def create_character(self, world: World, definition_id: str) -> GameObject:

        character_library = world.resource_manager.get_resource(CharacterLibrary)

        character_def = character_library.get_definition(definition_id)

        character = world.gameobject_manager.spawn_gameobject(
            components=character_def.components
        )
        character.metadata["definition_id"] = definition_id

        # Initialize the life span (Overwrite the existing one)
        species = character.get_component(Character).species
        rng = character.world.resource_manager.get_resource(random.Random)
        min_value, max_value = (int(x.strip()) for x in species.lifespan.split("-"))
        base_lifespan = rng.randint(min_value, max_value)
        character.get_component(Lifespan).stat.base_value = base_lifespan

        self._initialize_traits(character, character_def)

        for trait_id in species.traits:
            add_trait(character, trait_id)

        # Initialize the character's life stage given their age
        character.get_component(Character).life_stage = species.get_life_stage_for_age(
            int(character.get_component(Age).value)
        )

        return character

    def _initialize_traits(
        self, character: GameObject, definition: CharacterDef
    ) -> None:
        """Set the traits for a character."""
        rng = character.world.resource_manager.get_resource(random.Random)
        trait_library = character.world.resource_manager.get_resource(TraitLibrary)

        # species = character.get_component(Character).species

        # Loop through the trait entries in the definition and get by ID or select
        # randomly if using tags
        for entry in definition.traits:
            if entry.with_id:
                add_trait(character, entry.with_id)
            elif entry.with_tags:
                potential_traits = trait_library.get_definition_with_tags(
                    entry.with_tags
                )

                traits: list[str] = []
                trait_weights: list[int] = []

                for trait_def in potential_traits:
                    if trait_def.spawn_frequency >= 1:
                        traits.append(trait_def.definition_id)
                        trait_weights.append(trait_def.spawn_frequency)

                if len(traits) == 0:
                    continue

                chosen_trait = rng.choices(
                    population=traits, weights=trait_weights, k=1
                )[0]

                add_trait(character, chosen_trait)


class DefaultChildFactory(IChildFactory):
    """Default implementation of a child factory."""

    def create_child(
        self, birthing_parent: GameObject, other_parent: GameObject
    ) -> GameObject:

        world = birthing_parent.world

        character_library = world.resource_manager.get_resource(CharacterLibrary)

        child = character_library.factory.create_character(
            world, birthing_parent.metadata["definition_id"]
        )

        child.get_component(Character).last_name = birthing_parent.get_component(
            Character
        ).last_name

        return child
