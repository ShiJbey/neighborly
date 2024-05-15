"""Character Component Factories.

"""

import random
from typing import Any, ClassVar

from ordered_set import OrderedSet

from neighborly.components.character import Character, LifeStage, Sex, Species
from neighborly.components.shared import Age
from neighborly.components.skills import Skills
from neighborly.components.stats import Lifespan
from neighborly.components.traits import Trait, Traits
from neighborly.defs.base_types import CharacterDef
from neighborly.ecs import Component, ComponentFactory, GameObject, World
from neighborly.helpers.skills import add_skill, get_skill, has_skill
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
            first_name = name_factories.get_factory(name_factory)(world)

        last_name = ""
        if name := kwargs.get("last_name", ""):
            last_name = name
        elif name_factory := kwargs.get("last_name_factory", ""):
            last_name = name_factories.get_factory(name_factory)(world)

        sex: Sex = Sex[kwargs.get("sex", "NOT_SPECIFIED")]

        return Character(
            first_name=first_name,
            last_name=last_name,
            sex=sex,
        )


class SpeciesFactory(ComponentFactory):
    """Creates BelongsToSpecies component instances."""

    __component__ = "Species"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        species_id: str = kwargs["species"]
        species_library = world.resources.get_resource(SpeciesLibrary)
        species = species_library.get_species(species_id)

        return Species(species=species)


class DefaultCharacterFactory(ICharacterFactory):
    """Default implementation of a character factory."""

    def create_character(self, world: World, definition_id: str) -> GameObject:

        character_library = world.resource_manager.get_resource(CharacterLibrary)

        character_def = character_library.get_definition(definition_id)

        character = world.gameobject_manager.spawn_gameobject(
            components=character_def.components
        )
        character.metadata["definition_id"] = definition_id
        character.name = character.get_component(Character).full_name

        # Initialize the life span (Overwrite the existing one)
        species = character.get_component(Species).species
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

    N_INHERITED_TRAITS: ClassVar[int] = 3
    """The maximum number of traits to inherit from parents."""
    N_INHERITED_SKILLS: ClassVar[int] = 3
    """The maximum number of skills inherited from parents."""

    def create_child(
        self, birthing_parent: GameObject, other_parent: GameObject
    ) -> GameObject:

        world = birthing_parent.world
        rng = world.resources.get_resource(random.Random)
        character_library = world.resource_manager.get_resource(CharacterLibrary)
        name_factories = world.resources.get_resource(CharacterNameFactories)

        character_def = character_library.get_definition("child")
        child = world.gameobject_manager.spawn_gameobject(
            components=character_def.components
        )

        # Make sure they are a child
        child.get_component(Age).value = 0
        child.get_component(Character).life_stage = LifeStage.CHILD

        # Choose a species from the parents
        chosen_species = rng.choice(
            (
                birthing_parent.get_component(Species).species,
                other_parent.get_component(Species).species,
            )
        )

        child.add_component(Species(species=chosen_species))
        for trait_id in chosen_species.traits:
            add_trait(child, trait_id)

        # Initialize their lifespan from the species
        min_value, max_value = (
            int(x.strip()) for x in chosen_species.lifespan.split("-")
        )
        base_lifespan = rng.randint(min_value, max_value)
        child.get_component(Lifespan).stat.base_value = base_lifespan

        # Choose a sex
        chosen_sex = rng.choice((Sex.MALE, Sex.FEMALE))
        child.get_component(Character).sex = chosen_sex

        # Generate a first name using their gender and species as tags
        factory_tags = [
            "first",
            f"~{chosen_sex.name.lower()}",
            f"~{chosen_species.name.lower()}",
        ]
        name_factories = name_factories.get_with_tags(factory_tags)
        if not name_factories:
            raise RuntimeError(
                f"Cannot find first name factory with tags: {factory_tags}"
            )

        name_factory = rng.choice(name_factories)
        child.get_component(Character).first_name = name_factory(world)

        # Take the last name of the birthing parent
        child.get_component(Character).last_name = birthing_parent.get_component(
            Character
        ).last_name

        child.name = child.get_component(Character).full_name

        self._inherit_traits(
            birthing_parent=birthing_parent, other_parent=other_parent, child=child
        )

        self._initialize_traits(character=child, definition=character_def)

        self._initialize_skills(
            birthing_parent=birthing_parent, other_parent=other_parent, child=child
        )

        return child

    def _inherit_traits(
        self, birthing_parent: GameObject, other_parent: GameObject, child: GameObject
    ) -> None:
        """Set the traits for a character."""
        world = birthing_parent.world
        rng = world.resources.get_resource(random.Random)
        trait_library = world.resources.get_resource(TraitLibrary)
        birthing_parent_traits = birthing_parent.get_component(Traits)
        other_parent_traits = other_parent.get_component(Traits)

        all_trait_ids = OrderedSet(
            [*birthing_parent_traits.traits.keys(), *other_parent_traits.traits.keys()]
        )

        # Get full pool of potential traits
        inheritable_traits: list[Trait] = []

        for trait_id in all_trait_ids:
            birthing_parent_has_trait = trait_id in birthing_parent_traits.traits
            other_parent_has_trait = trait_id in other_parent_traits.traits

            one_parent_has_trait = birthing_parent_has_trait or other_parent_has_trait
            both_parents_have_trait = (
                birthing_parent_has_trait and other_parent_has_trait
            )

            trait = trait_library.get_trait(trait_id)

            if not trait.is_inheritable:
                continue

            if both_parents_have_trait and rng.random() < trait.inheritance_chance_both:
                inheritable_traits.append(trait)

            elif (
                one_parent_has_trait and rng.random() < trait.inheritance_chance_single
            ):
                inheritable_traits.append(trait)

        if not inheritable_traits:
            return

        # Select a subset
        sampled_traits = rng.sample(
            inheritable_traits, min(self.N_INHERITED_TRAITS, len(inheritable_traits))
        )
        for trait in sampled_traits:
            add_trait(child, trait)

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

    def _initialize_skills(
        self, birthing_parent: GameObject, other_parent: GameObject, child: GameObject
    ) -> None:
        """Set the skills for a character."""

        world = birthing_parent.world
        rng = world.resources.get_resource(random.Random)
        birthing_parent_skills = birthing_parent.get_component(Skills)
        other_parent_skills = other_parent.get_component(Skills)

        all_skill_ids = OrderedSet(
            [*birthing_parent_skills.skills.keys(), *other_parent_skills.skills.keys()]
        )

        if not all_skill_ids:
            return

        # Select a subset
        sampled_skills = rng.sample(
            all_skill_ids, min(self.N_INHERITED_SKILLS, len(all_skill_ids))
        )
        for skill_id in sampled_skills:
            base_value: float = 0

            if has_skill(birthing_parent, skill_id):
                base_value += get_skill(birthing_parent, skill_id).stat.base_value

            if has_skill(other_parent, skill_id):
                base_value += get_skill(other_parent, skill_id).stat.base_value

            base_value = base_value / 2

            add_skill(child, skill_id, base_value=base_value)
