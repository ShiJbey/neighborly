"""Character Factory.

"""

from abc import ABC, abstractmethod

import pydantic

from neighborly.components.character import Character, Sex
from neighborly.components.location import FrequentedLocations
from neighborly.components.relationship import Relationships
from neighborly.components.shared import Agent, PersonalEventHistory
from neighborly.components.skills import Skills
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits
from neighborly.defs.base_types import CharacterDef
from neighborly.ecs import World
from neighborly.ecs.game_object import GameObject
from neighborly.libraries import TraitLibrary
from neighborly.tracery import Tracery


class CharacterGenerationOptions(pydantic.BaseModel):
    """Generation parameters for creating characters."""

    definition_id: str
    """The definition to use for generation."""
    first_name: str = ""
    """The character's first name."""
    last_name: str = ""
    """The character's last name/surname/family name."""
    age: int = -1
    """The character's age (overrides life_stage)."""
    life_stage: str = ""
    """The life stage of the character."""


class CharacterFactory:
    """Generates characters from definitions."""

    def instantiate(
        self,
        world: World,
        character_def: CharacterDef,
        options: CharacterGenerationOptions,
    ) -> GameObject:
        """Generate a new character."""

        character = world.gameobjects.spawn_gameobject()
        character.metadata["definition_id"] = options.definition_id

        character.add_component(Agent("character"))
        character.add_component(Traits())
        character.add_component(Skills())
        character.add_component(Stats())
        character.add_component(FrequentedLocations())
        character.add_component(Relationships())
        character.add_component(PersonalEventHistory())

        species_id = world.rng.choice(self.species)

        library = character.world.resources.get_resource(TraitLibrary)
        species = library.get_trait(species_id)

        character.add_component(
            Character(
                first_name="",
                last_name="",
                sex=Sex[character_def.sex],
                species=species,
            )
        )

        self._initialize_name(character, options)
        self._initialize_character_age(character, options)
        self._initialize_character_stats(character, options)
        self._initialize_traits(character, options)
        self._initialize_character_skills(character)

        raise NotImplementedError()

    def _initialize_name(
        self, character: GameObject, options: CharacterGenerationOptions
    ) -> None:
        """Initialize the character's name.

        Parameters
        ----------
        character
            The character to initialize.
        """
        character_comp = character.get_component(Character)

        character_comp.first_name = self.generate_first_name(
            character, default_first_name
        )
        character_comp.last_name = self.generate_last_name(character, default_last_name)

    def _initialize_character_age(
        self, character: GameObject, options: CharacterGenerationOptions
    ) -> None:
        """Initializes the characters age."""
        rng = character.world.resources.get_resource(random.Random)
        life_stage: Optional[LifeStage] = kwargs.get("life_stage")
        character_comp = character.get_component(Character)
        species = character.get_component(Character).species.get_component(Species)

        if life_stage is not None:
            character_comp.life_stage = life_stage

            # Generate an age for this character
            if life_stage == LifeStage.CHILD:
                character_comp.age = rng.randint(0, species.adolescent_age - 1)
            elif life_stage == LifeStage.ADOLESCENT:
                character_comp.age = rng.randint(
                    species.adolescent_age,
                    species.young_adult_age - 1,
                )
            elif life_stage == LifeStage.YOUNG_ADULT:
                character_comp.age = rng.randint(
                    species.young_adult_age,
                    species.adult_age - 1,
                )
            elif life_stage == LifeStage.ADULT:
                character_comp.age = rng.randint(
                    species.adult_age,
                    species.senior_age - 1,
                )
            else:
                character_comp.age = character_comp.age = rng.randint(
                    species.senior_age,
                    species.lifespan - 1,
                )

    def _initialize_traits(
        self, character: GameObject, options: CharacterGenerationOptions
    ) -> None:
        """Set the traits for a character."""
        character.add_component(Traits())
        rng = character.world.resources.get_resource(random.Random)
        trait_library = character.world.resources.get_resource(TraitLibrary)

        traits: list[str] = []
        trait_weights: list[int] = []

        for trait_id in trait_library.trait_ids:
            trait_def = trait_library.get_definition(trait_id)
            if trait_def.spawn_frequency >= 1:
                traits.append(trait_id)
                trait_weights.append(trait_def.spawn_frequency)

        if len(traits) == 0:
            return

        max_traits = kwargs.get("n_traits", self.max_traits)

        chosen_traits = rng.choices(traits, trait_weights, k=max_traits)

        for trait in chosen_traits:
            add_trait(character, trait)

        default_traits: list[str] = kwargs.get("default_traits", [])

        for trait in default_traits:
            add_trait(character, trait)

    def _initialize_character_stats(
        self, character: GameObject, options: CharacterGenerationOptions
    ) -> None:
        """Initializes a characters stats with random values."""
        rng = character.world.resources.get_resource(random.Random)

        character_comp = character.get_component(Character)
        species = character.get_component(Character).species.get_component(Species)

        health = add_stat(
            character, "health", Stat(base_value=1000, bounds=(0, 999_999))
        )
        health_decay = add_stat(
            character,
            "health_decay",
            Stat(base_value=1000.0 / species.lifespan, bounds=(0, 999_999)),
        )
        fertility = add_stat(
            character,
            "fertility",
            Stat(base_value=round(rng.uniform(0.0, 1.0)), bounds=(0, 1.0)),
        )
        add_stat(
            character,
            "boldness",
            Stat(
                base_value=float(rng.randint(0, 255)), bounds=(0, 255), is_discrete=True
            ),
        )
        add_stat(
            character,
            "stewardship",
            Stat(
                base_value=float(rng.randint(0, 255)), bounds=(0, 255), is_discrete=True
            ),
        )
        add_stat(
            character,
            "sociability",
            Stat(
                base_value=float(rng.randint(0, 255)), bounds=(0, 255), is_discrete=True
            ),
        )
        add_stat(
            character,
            "attractiveness",
            Stat(
                base_value=float(rng.randint(0, 255)), bounds=(0, 255), is_discrete=True
            ),
        )
        add_stat(
            character,
            "intelligence",
            Stat(
                base_value=float(rng.randint(0, 255)), bounds=(0, 255), is_discrete=True
            ),
        )
        add_stat(
            character,
            "reliability",
            Stat(
                base_value=float(rng.randint(0, 255)), bounds=(0, 255), is_discrete=True
            ),
        )

        # Adjust health for current age
        health.base_value -= character_comp.age * health_decay.value

        # Adjust fertility for current life stage
        if character_comp.sex == Sex.MALE:
            if character_comp.life_stage == LifeStage.SENIOR:
                fertility.base_value = fertility.base_value * 0.5
            if character_comp.life_stage == LifeStage.ADULT:
                fertility.base_value = fertility.base_value * 0.8
        elif character_comp.sex == Sex.FEMALE:
            if character_comp.life_stage == LifeStage.SENIOR:
                fertility.base_value = 0
            if character_comp.life_stage == LifeStage.ADULT:
                fertility.base_value = fertility.base_value * 0.4

        # Override the generate values use specified values
        stat_overrides: dict[str, float] = kwargs.get("stats", {})

        for stat, override_value in stat_overrides.items():
            get_stat(character, stat).base_value = override_value

    def _initialize_character_skills(self, character: GameObject) -> None:
        """Add default skills to the character."""
        rng = character.world.resources.get_resource(random.Random)
        for skill_id, interval in self.default_skills.items():
            value = rng.randint(interval[0], interval[1])
            add_skill(character, skill_id, value)

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
    def generate(self, options: CharacterGenerationOptions) -> str:
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

    def generate(self, options: CharacterGenerationOptions) -> str:
        """Generates a last name for a character."""
        if options.first_name:
            return options.first_name

        return ""


class LastNameFactory:
    """Generates a last name for a character."""

    def generate(self, options: CharacterGenerationOptions) -> str:
        """Generates a last name for a character."""
        raise NotImplementedError()
