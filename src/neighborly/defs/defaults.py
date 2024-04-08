"""Default Content Definitions.

This module contains default implementations of concrete definition classes that
inherit from those found in neighborly.defs.base_types. These definitions are loaded
into ever Neighborly instance when it is constructed.

"""

from __future__ import annotations

import random
from typing import Callable, ClassVar, Optional, cast

from neighborly.components.business import Business, JobOpeningData
from neighborly.components.character import Character, LifeStage, Sex
from neighborly.components.location import (
    FrequentedLocations,
    Location,
    LocationPreferences,
)
from neighborly.components.relationship import Relationships, SocialRules
from neighborly.components.residence import ResidentialBuilding, ResidentialUnit, Vacant
from neighborly.components.settlement import District, Settlement
from neighborly.components.shared import Age, Agent
from neighborly.components.skills import Skills
from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    BusinessSpawnTableEntry,
    CharacterSpawnTable,
    CharacterSpawnTableEntry,
    ResidenceSpawnTable,
    ResidenceSpawnTableEntry,
)
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits
from neighborly.defs.base_types import (
    BusinessDef,
    BusinessGenOptions,
    CharacterDef,
    CharacterGenOptions,
    DistrictDef,
    DistrictGenOptions,
    JobRoleDef,
    ResidenceDef,
    ResidenceGenOptions,
    SettlementDef,
    SettlementGenOptions,
    SkillDef,
    SpeciesDef,
    TraitDef,
)
from neighborly.ecs import GameObject, World
from neighborly.helpers.character import set_species
from neighborly.helpers.settlement import create_district
from neighborly.helpers.skills import add_skill
from neighborly.helpers.stats import add_stat, get_stat, has_stat
from neighborly.helpers.traits import add_trait
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    JobRoleLibrary,
    ResidenceLibrary,
    SkillLibrary,
    TraitLibrary,
)
from neighborly.life_event import PersonalEventHistory
from neighborly.tracery import Tracery


class DefaultSkillDef(SkillDef):
    """The default implementation of a skill definition."""

    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError()


class DefaultTraitDef(TraitDef):
    """A definition for a trait type."""

    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError()


class DefaultSpeciesDef(SpeciesDef):
    """A definition for a trait type."""

    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError()


def default_district_name_factory(world: World, _: DistrictGenOptions) -> str:
    """Generate a new name"""
    tracery = world.resource_manager.get_resource(Tracery)
    name = tracery.generate("#settlement_name#")
    return name


class DefaultDistrictDef(DistrictDef):
    """A definition for a district type specified by the user."""

    name_factories: ClassVar[dict[str, Callable[[World, DistrictGenOptions], str]]] = {
        "default": default_district_name_factory
    }

    def instantiate(
        self,
        world: World,
        settlement: GameObject,
        options: DistrictGenOptions,
    ) -> GameObject:
        district = world.gameobject_manager.spawn_gameobject()
        district.metadata["definition_id"] = self.definition_id

        name = ""

        if self.name:
            name = self.name
        elif self.name_factory:
            name = self.name_factories[self.name_factory](world, options)

        district.add_component(
            District(
                gameobject=district,
                name=name,
                description=self.description,
                settlement=settlement,
                residential_slots=self.residential_slots,
                business_slots=self.business_slots,
            )
        )
        district.add_component(Agent(gameobject=district, agent_type="district"))

        self.initialize_business_spawn_table(district)
        self.initialize_character_spawn_table(district)
        self.initialize_residence_spawn_table(district)

        return district

    def initialize_business_spawn_table(self, district: GameObject) -> None:
        """Create the business spawn table for the district."""
        world = district.world
        rng = world.resource_manager.get_resource(random.Random)
        business_library = world.resource_manager.get_resource(BusinessLibrary)

        table_entries: list[BusinessSpawnTableEntry] = []

        for entry in self.business_types:
            if entry.with_id:
                business_def = business_library.get_definition(entry.with_id)
                table_entries.append(
                    BusinessSpawnTableEntry(
                        name=entry.with_id,
                        spawn_frequency=business_def.spawn_frequency,
                        max_instances=business_def.max_instances,
                        min_population=business_def.min_population,
                        instances=0,
                    )
                )
            elif entry.with_tags:
                potential_defs = business_library.get_definition_with_tags(
                    entry.with_tags
                )

                if not potential_defs:
                    continue

                business_def = rng.choice(potential_defs)

                table_entries.append(
                    BusinessSpawnTableEntry(
                        name=business_def.definition_id,
                        spawn_frequency=entry.spawn_frequency,
                        max_instances=entry.max_instances,
                        min_population=entry.min_population,
                        instances=0,
                    )
                )

        district.add_component(BusinessSpawnTable(district, entries=table_entries))

    def initialize_character_spawn_table(self, district: GameObject) -> None:
        """Create the character spawn table for the district."""
        world = district.world
        rng = world.resource_manager.get_resource(random.Random)

        character_library = world.resource_manager.get_resource(CharacterLibrary)

        table_entries: list[CharacterSpawnTableEntry] = []

        for entry in self.character_types:
            if entry.with_id:

                character_def = character_library.get_definition(entry.with_id)

                table_entries.append(
                    CharacterSpawnTableEntry(
                        name=character_def.definition_id,
                        spawn_frequency=entry.spawn_frequency,
                    )
                )

            elif entry.with_id:

                potential_defs = character_library.get_definition_with_tags(
                    entry.with_tags
                )

                if not potential_defs:
                    continue

                character_def = rng.choice(potential_defs)

                table_entries.append(
                    CharacterSpawnTableEntry(
                        name=character_def.definition_id,
                        spawn_frequency=entry.spawn_frequency,
                    )
                )

        district.add_component(CharacterSpawnTable(district, entries=table_entries))

    def initialize_residence_spawn_table(self, district: GameObject) -> None:
        """Create the residence spawn table for the district."""
        world = district.world
        rng = world.resource_manager.get_resource(random.Random)

        residence_library = world.resource_manager.get_resource(ResidenceLibrary)

        table_entries: list[ResidenceSpawnTableEntry] = []

        for entry in self.residence_types:
            if entry.with_id:
                residence_def = residence_library.get_definition(entry.with_id)

                table_entries.append(
                    ResidenceSpawnTableEntry(
                        name=residence_def.definition_id,
                        spawn_frequency=residence_def.spawn_frequency,
                        instances=0,
                        required_population=residence_def.required_population,
                        max_instances=residence_def.max_instances,
                        is_multifamily=residence_def.is_multifamily,
                    )
                )

            elif entry.with_tags:

                potential_defs = residence_library.get_definition_with_tags(
                    entry.with_tags
                )

                if not potential_defs:
                    continue

                residence_def = rng.choice(potential_defs)

                table_entries.append(
                    ResidenceSpawnTableEntry(
                        name=residence_def.definition_id,
                        spawn_frequency=residence_def.spawn_frequency,
                        instances=0,
                        required_population=residence_def.required_population,
                        max_instances=residence_def.max_instances,
                        is_multifamily=residence_def.is_multifamily,
                    )
                )

        district.add_component(ResidenceSpawnTable(district, entries=table_entries))


def default_settlement_name_factory(world: World, _: SettlementGenOptions) -> str:
    """Generate a new name"""
    tracery = world.resource_manager.get_resource(Tracery)
    name = tracery.generate("#settlement_name#")
    return name


class DefaultSettlementDef(SettlementDef):
    """A definition for a settlement type specified by the user."""

    name_factories: ClassVar[
        dict[str, Callable[[World, SettlementGenOptions], str]]
    ] = {"default": default_settlement_name_factory}

    def instantiate(self, world: World, options: SettlementGenOptions) -> GameObject:
        settlement = world.gameobject_manager.spawn_gameobject()
        settlement.metadata["definition_id"] = self.definition_id

        name = ""

        if self.name:
            name = self.name

        elif self.name_factory:
            name = self.name_factories[self.name_factory](world, options)

        settlement.add_component(Settlement(settlement, name=name))
        settlement.add_component(
            Agent(
                gameobject=settlement,
                agent_type="settlement",
            )
        )
        settlement.add_component(PersonalEventHistory(settlement))

        self.initialize_districts(settlement)
        return settlement

    def initialize_districts(self, settlement: GameObject) -> None:
        """Instantiates the settlement's districts."""

        library = settlement.world.resource_manager.get_resource(DistrictLibrary)
        rng = settlement.world.resource_manager.get_resource(random.Random)

        for district_entry in self.districts:
            if district_entry.with_id:
                district = create_district(
                    settlement.world,
                    settlement,
                    district_entry.with_id,
                )
                settlement.add_child(district)
            elif district_entry.with_tags:
                matching_districts = library.get_definition_with_tags(
                    district_entry.with_tags
                )

                if matching_districts:
                    chosen_district = rng.choice(matching_districts)
                    district = create_district(
                        settlement.world,
                        settlement,
                        chosen_district.definition_id,
                    )
                    settlement.add_child(district)


class DefaultResidenceDef(ResidenceDef):
    """A default implementation of a Residence Definition."""

    def instantiate(
        self, world: World, district: GameObject, options: ResidenceGenOptions
    ) -> GameObject:

        residence = world.gameobject_manager.spawn_gameobject()
        residence.metadata["definition_id"] = self.definition_id

        world = residence.world

        building = residence.add_component(
            ResidentialBuilding(residence, district=district)
        )
        residence.add_component(Traits(residence))
        residence.add_component(Stats(residence))

        residence.name = self.name

        for _ in range(self.residential_units):
            residential_unit = world.gameobject_manager.spawn_gameobject(
                name="ResidentialUnit"
            )
            residential_unit.add_component(Traits(residential_unit))
            residence.add_child(residential_unit)
            residential_unit.add_component(
                ResidentialUnit(residential_unit, building=residence, district=district)
            )
            residential_unit.add_component(Location(residential_unit, is_private=True))
            building.add_residential_unit(residential_unit)
            residential_unit.add_component(Vacant(residential_unit))

        return residence


def generate_any_first_name(world: World, _: CharacterGenOptions) -> str:
    """Generate a first name for a character"""

    tracery = world.resource_manager.get_resource(Tracery)
    rng = world.resource_manager.get_resource(random.Random)

    pattern = rng.choice(["#first_name::feminine#", "#first_name::masculine#"])

    name = tracery.generate(pattern)

    return name


def generate_masculine_first_name(world: World, _: CharacterGenOptions) -> str:
    """Generate a masculine first name for a character"""

    tracery = world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#first_name::masculine#")

    return name


def generate_feminine_first_name(world: World, _: CharacterGenOptions) -> str:
    """Generate a feminine first name for a character"""

    tracery = world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#first_name::feminine#")

    return name


def generate_last_name(world: World, _: CharacterGenOptions) -> str:
    """Generate a last_name for a character."""

    tracery = world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#last_name#")

    return name


class DefaultCharacterDef(CharacterDef):
    """Default implementation for character definitions."""

    first_name_factories: ClassVar[
        dict[str, Callable[[World, CharacterGenOptions], str]]
    ] = {
        "default": generate_any_first_name,
        "masculine": generate_masculine_first_name,
        "feminine": generate_feminine_first_name,
    }

    last_name_factories: ClassVar[
        dict[str, Callable[[World, CharacterGenOptions], str]]
    ] = {"default": generate_last_name}

    STAT_MAX_VALUE: ClassVar[int] = 100

    def instantiate(
        self,
        world: World,
        options: CharacterGenOptions,
    ) -> GameObject:

        character = world.gameobject_manager.spawn_gameobject()
        character.metadata["definition_id"] = self.definition_id

        rng = world.resource_manager.get_resource(random.Random)

        library = character.world.resource_manager.get_resource(TraitLibrary)
        species = library.get_definition(self.species)

        character.add_component(
            Character(
                character,
                first_name="",
                last_name="",
                sex=rng.choice((Sex.MALE, Sex.FEMALE)),
                species=cast(SpeciesDef, species),
            )
        )
        character.add_component(Agent(gameobject=character, agent_type="character"))
        character.add_component(Age(character))
        character.add_component(Traits(character))
        character.add_component(Skills(character))
        character.add_component(Stats(character))
        character.add_component(FrequentedLocations(character))
        character.add_component(Relationships(character))
        character.add_component(LocationPreferences(character))
        character.add_component(SocialRules(character))
        character.add_component(PersonalEventHistory(character))

        self.initialize_name(character, options)
        self.initialize_character_age(character, options)
        self.initialize_character_stats(character)
        self.initialize_traits(character, options)
        self.initialize_character_skills(character)

        return character

    def initialize_name(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Initialize the character's name.

        Parameters
        ----------
        character
            The character to initialize.
        """
        character_comp = character.get_component(Character)

        if options.first_name:
            character_comp.first_name = options.first_name
        else:
            factory = self.first_name_factories[self.first_name_factory]
            character_comp.first_name = factory(character.world, options)

        if options.last_name:
            character_comp.last_name = options.last_name
        else:
            factory = self.last_name_factories[self.last_name_factory]
            character_comp.last_name = factory(character.world, options)

    def initialize_character_age(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Initializes the characters age."""
        rng = character.world.resource_manager.get_resource(random.Random)

        character_comp = character.get_component(Character)
        age = character.get_component(Age)
        species = character.get_component(Character).species

        if options.life_stage is not "":

            life_stage: Optional[LifeStage] = LifeStage[options.life_stage]

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

    def initialize_traits(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Set the traits for a character."""
        character.add_component(Traits(character))
        rng = character.world.resource_manager.get_resource(random.Random)
        trait_library = character.world.resource_manager.get_resource(TraitLibrary)

        set_species(character, self.species)

        # Loop through the trait entries in the definition and get by ID or select
        # randomly if using tags
        for entry in self.traits:
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

        # Add traits specified in options
        for trait in options.traits:
            add_trait(character, trait)

    def initialize_character_stats(self, character: GameObject) -> None:
        """Initializes a characters stats with random values."""
        rng = character.world.resource_manager.get_resource(random.Random)

        # Initialize the life span
        species = character.get_component(Character).species
        rng = character.world.resource_manager.get_resource(random.Random)
        min_value, max_value = (int(x.strip()) for x in species.lifespan.split("-"))
        base_lifespan = rng.randint(min_value, max_value)

        add_stat(
            character,
            "lifespan",
            base_value=base_lifespan,
            bounds=(0, 999_999),
            is_discrete=True,
        )

        add_stat(
            character,
            "fertility",
            base_value=float(rng.uniform(0, self.STAT_MAX_VALUE)),
            bounds=(0, self.STAT_MAX_VALUE),
        )

        add_stat(
            character,
            "kindness",
            base_value=float(rng.randint(0, self.STAT_MAX_VALUE)),
            bounds=(0, self.STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "courage",
            base_value=float(rng.randint(0, self.STAT_MAX_VALUE)),
            bounds=(0, self.STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "stewardship",
            base_value=float(rng.randint(0, self.STAT_MAX_VALUE)),
            bounds=(0, self.STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "sociability",
            base_value=float(rng.randint(0, self.STAT_MAX_VALUE)),
            bounds=(0, self.STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "intelligence",
            base_value=float(rng.randint(0, self.STAT_MAX_VALUE)),
            bounds=(0, self.STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "discipline",
            base_value=float(rng.randint(0, self.STAT_MAX_VALUE)),
            bounds=(0, self.STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "charm",
            base_value=float(rng.randint(0, self.STAT_MAX_VALUE)),
            bounds=(0, self.STAT_MAX_VALUE),
            is_discrete=True,
        )

        # Override the default stat base values.
        for entry in self.stats:
            base_value = 0

            if entry.value is not None:
                base_value = entry.value

            elif entry.value_range:
                min_value, max_value = (
                    int(x.strip()) for x in entry.value_range.split("-")
                )
                base_value = rng.randint(min_value, max_value)

            if not has_stat(character, entry.stat):
                raise ValueError(
                    f"[def ({self.definition_id})] Character does not have "
                    f"{entry.stat!r} stat."
                )

            get_stat(character, entry.stat).base_value = base_value

    def initialize_character_skills(self, character: GameObject) -> None:
        """Add default skills to the character."""
        rng = character.world.resource_manager.get_resource(random.Random)
        skill_library = character.world.resource_manager.get_resource(SkillLibrary)

        for entry in self.skills:
            base_value = 0
            if entry.value is not None:
                base_value = entry.value
            elif entry.value_range:
                min_value, max_value = (
                    int(x.strip()) for x in entry.value_range.split("-")
                )
                base_value = rng.randint(min_value, max_value)

            if entry.with_id:
                add_skill(character, entry.with_id, base_value=base_value)

            elif entry.with_tags:
                potential_skills = skill_library.get_definition_with_tags(
                    entry.with_tags
                )

                if not potential_skills:
                    continue

                chosen_skill = rng.choice(potential_skills)

                add_skill(character, chosen_skill.definition_id, base_value=base_value)


class DefaultJobRoleDef(JobRoleDef):
    """A default implementation of a Job Role Definition."""

    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError()


class DefaultBusinessDef(BusinessDef):
    """A default implementation of a Business Definition."""

    name_factories: ClassVar[dict[str, Callable[[World, BusinessGenOptions], str]]] = {}

    def instantiate(
        self, world: World, district: GameObject, options: BusinessGenOptions
    ) -> GameObject:

        business = world.gameobject_manager.spawn_gameobject()
        business.metadata["definition_id"] = self.definition_id

        job_role_library = world.resource_manager.get_resource(JobRoleLibrary)

        business.add_component(
            Business(
                business,
                name="",
                owner_role=job_role_library.get_definition(self.owner_role),
                employee_roles={
                    role: JobOpeningData(
                        role_id=role,
                        business_id=business.uid,
                        count=count,
                    )
                    for role, count in self.employee_roles.items()  # pylint: disable=E1101
                },
                district=district,
            )
        )
        business.add_component(Agent(gameobject=business, agent_type="business"))
        business.add_component(Traits(business))
        business.add_component(Location(business, is_private=not self.open_to_public))
        business.add_component(PersonalEventHistory(business))
        business.add_component(Stats(business))
        business.add_component(Relationships(business))
        business.add_component(SocialRules(business))
        business.add_component(Age(business))

        # Initialize the life span
        rng = world.resource_manager.get_resource(random.Random)
        min_value, max_value = (int(x.strip()) for x in self.lifespan.split("-"))
        base_lifespan = rng.randint(min_value, max_value)
        add_stat(business, "lifespan", base_value=base_lifespan, is_discrete=True)

        self.generate_name(business, options)

        for trait in self.traits:
            add_trait(business, trait)

        return business

    def generate_name(self, business: GameObject, options: BusinessGenOptions) -> None:
        """Generates a name for the business."""
        if options.name:
            business.get_component(Business).name = options.name

        elif self.name:
            business.get_component(Business).name = self.name

        elif self.name_factory:
            name = self.name_factories[self.name_factory](business.world, options)
            business.get_component(Business).name = name
