"""Character Factory.

"""

from abc import ABC, abstractmethod
from typing import cast

from neighborly.components.character import Character, LifeStage, Sex
from neighborly.components.location import FrequentedLocations
from neighborly.components.shared import Age, Agent, EventHistory
from neighborly.components.skills import Skills
from neighborly.components.stats import StatEntry, Stats
from neighborly.components.traits import Traits
from neighborly.defs.base_types import CharacterDef, CharacterGenOptions
from neighborly.defs.species import SpeciesDef
from neighborly.ecs import GameObject, World
from neighborly.helpers.skills import add_skill
from neighborly.helpers.stats import add_stat
from neighborly.helpers.traits import add_trait
from neighborly.libraries import SkillLibrary, TraitLibrary
from neighborly.tracery import Tracery


class DefaultCharacterDef(CharacterDef):
    """Generates characters from definitions."""

    def instantiate(
        self,
        world: World,
        options: CharacterGenOptions,
    ) -> GameObject:

        character = GameObject.create_new(world)
        character.metadata["definition_id"] = options.definition_id

        character.add_component(Agent, agent_type="character")
        character.add_component(Traits)
        character.add_component(Skills)
        character.add_component(Stats)
        character.add_component(FrequentedLocations)
        character.add_component(EventHistory)

        species_id = world.rng.choice(self.species)

        library = character.world.resources.get_resource(TraitLibrary)
        species = library.get_definition(species_id)

        character.add_component(
            Character,
            first_name="",
            last_name="",
            sex=Sex[self.sex],
            species=species,
        )

        self._initialize_name(character, options)
        self._initialize_character_age(character, options)
        self._initialize_character_stats(character, options)
        self._initialize_traits(character, options)
        self._initialize_character_skills(character)

        return character

    def _initialize_name(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Initialize the character's name.

        Parameters
        ----------
        character
            The character to initialize.
        """
        character_comp = character.get_component(Character)

        character_comp.name = self.generate_first_name(character, options.first_name)
        character_comp.last_name = self.generate_last_name(character, options.last_name)

    def _initialize_character_age(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Initializes the characters age."""
        rng = character.world.rng
        character_comp = character.get_component(Character)
        age_comp = character.get_component(Age)

        species = cast(
            SpeciesDef,
            character.world.resources.get_resource(TraitLibrary).get_definition(
                character_comp.species
            ),
        )

        if options.life_stage:
            character_comp.life_stage = LifeStage[options.life_stage]

            # Generate an age for this character
            if character_comp.life_stage == LifeStage.CHILD:
                age_comp.value = rng.randint(0, species.adolescent_age - 1)
            elif character_comp.life_stage == LifeStage.ADOLESCENT:
                age_comp.value = rng.randint(
                    species.adolescent_age,
                    species.young_adult_age - 1,
                )
            elif character_comp.life_stage == LifeStage.YOUNG_ADULT:
                age_comp.value = rng.randint(
                    species.young_adult_age,
                    species.adult_age - 1,
                )
            elif character_comp.life_stage == LifeStage.ADULT:
                age_comp.value = rng.randint(
                    species.adult_age,
                    species.senior_age - 1,
                )
            else:
                age_comp.value = age_comp.value = rng.randint(
                    species.senior_age,
                    species.lifespan - 1,
                )

    def _initialize_traits(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Set the traits for a character."""
        character.add_component(Traits)
        rng = character.world.rng
        trait_library = character.world.resources.get_resource(TraitLibrary)

        traits: list[str] = []
        trait_weights: list[int] = []

        for trait_def in trait_library.definitions.values():
            if trait_def.spawn_frequency >= 1:
                traits.append(trait_def.definition_id)
                trait_weights.append(trait_def.spawn_frequency)

        if len(traits) == 0:
            return

        chosen_traits = rng.choices(traits, trait_weights, k=3)

        for trait in chosen_traits:
            add_trait(character, trait)

        for entry in self.traits:
            if entry.with_id:
                add_trait(character, entry.with_id)

            elif entry.with_id:
                potential_traits = trait_library.get_definition_with_tags(
                    entry.with_tags
                )

                if not potential_traits:
                    continue

                trait_def = character.world.rng.choice(potential_traits)

                add_trait(character, trait_def.definition_id)

    def _initialize_character_stats(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Initializes a characters stats with random values."""
        rng = character.world.rng

        species_id = character.get_component(Character).species

        species = cast(
            SpeciesDef,
            character.world.resources.get_resource(TraitLibrary).get_definition(
                species_id
            ),
        )

        add_stat(
            character,
            StatEntry(
                name="lifespan",
                base_value=species.lifespan,
                min_value=0,
                max_value=999_999,
                is_discrete=True,
            ),
        )

        add_stat(
            character,
            StatEntry(
                name="fertility",
                base_value=float(rng.uniform(0.0, 1.0)),
                min_value=0,
                max_value=1.0,
                is_discrete=True,
            ),
        )

        add_stat(
            character,
            StatEntry(
                name="boldness",
                base_value=float(rng.randint(0, 255)),
                min_value=0,
                max_value=255,
                is_discrete=True,
            ),
        )

        add_stat(
            character,
            StatEntry(
                name="stewardship",
                base_value=float(rng.randint(0, 255)),
                min_value=0,
                max_value=255,
                is_discrete=True,
            ),
        )

        add_stat(
            character,
            StatEntry(
                name="sociability",
                base_value=float(rng.randint(0, 255)),
                min_value=0,
                max_value=255,
                is_discrete=True,
            ),
        )

        add_stat(
            character,
            StatEntry(
                name="attractiveness",
                base_value=float(rng.randint(0, 255)),
                min_value=0,
                max_value=255,
                is_discrete=True,
            ),
        )

        add_stat(
            character,
            StatEntry(
                name="intelligence",
                base_value=float(rng.randint(0, 255)),
                min_value=0,
                max_value=255,
                is_discrete=True,
            ),
        )

        add_stat(
            character,
            StatEntry(
                name="reliability",
                base_value=float(rng.randint(0, 255)),
                min_value=0,
                max_value=255,
                is_discrete=True,
            ),
        )

        for stat_data in self.stats:
            stat_value = 0

            if stat_data.value is not None:
                stat_value = stat_data.value

            elif stat_data.value_range:
                range_min, range_max = tuple[float, ...](
                    float(val.strip()) for val in stat_data.value_range.split()
                )

                stat_value = ((range_max - range_min) * rng.random()) + range_min

            add_stat(
                character,
                StatEntry(
                    name=stat_data.stat,
                    base_value=stat_value,
                    bounds=(stat_data.min_value, stat_data.max_value),
                    is_discrete=stat_data.is_discrete,
                ),
            )

    def _initialize_character_skills(self, character: GameObject) -> None:
        """Add default skills to the character."""
        for entry in self.skills:
            skill_value = 0

            if entry.value is not None:
                skill_value = entry.value

            elif entry.value_range:
                range_min, range_max = tuple[float, ...](
                    float(val.strip()) for val in entry.value_range.split()
                )

                skill_value = (
                    (range_max - range_min) * character.world.rng.random()
                ) + range_min

            if entry.with_id:
                add_skill(
                    gameobject=character, skill_id=entry.with_id, base_value=skill_value
                )

            elif entry.with_tags:
                skill_library = character.world.resources.get_resource(SkillLibrary)
                potential_defs = skill_library.get_definition_with_tags(entry.with_tags)

                if not potential_defs:
                    continue

                skill_def = character.world.rng.choice(potential_defs)

                add_skill(
                    gameobject=character,
                    skill_id=skill_def.definition_id,
                    base_value=skill_value,
                )

    @staticmethod
    def generate_first_name(character: GameObject, pattern: str) -> str:
        """Generates a first name for the character"""

        tracery = character.world.resources.get_resource(Tracery)

        if pattern:
            name = tracery.generate(pattern)
        elif character.get_component(Character).sex == Sex.MALE:
            name = tracery.generate("#first_name::masculine#")
        else:
            name = tracery.generate("#first_name::feminine#")

        return name

    @staticmethod
    def generate_last_name(character: GameObject, pattern: str) -> str:
        """Generates a last_name for the character."""

        tracery = character.world.resources.get_resource(Tracery)

        if pattern:
            name = tracery.generate(pattern)
        else:
            name = tracery.generate("#last_name#")

        return name


class ICharacterNameFactory(ABC):
    """Generates a part of a character's name"""

    @abstractmethod
    def generate(self, options: CharacterGenOptions) -> str:
        """Generates a last name for a character."""
        raise NotImplementedError()


class FirstNameFactory:
    """Generates a first name for a character."""

    __slots__ = ("factories",)

    factories: dict[str, ICharacterNameFactory]
    """Factories this factory samples from."""

    def add_factory(self, name: str, factory: ICharacterNameFactory) -> None:
        """Add a new sub factory for first name generation."""
        self.factories[name] = factory

    def generate(self, options: CharacterGenOptions) -> str:
        """Generates a last name for a character."""
        if options.first_name:
            return options.first_name

        return ""


class LastNameFactory:
    """Generates a last name for a character."""

    def generate(self, options: CharacterGenOptions) -> str:
        """Generates a last name for a character."""
        raise NotImplementedError()
