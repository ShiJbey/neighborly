"""Default Content Definitions.

This module contains default implementations of concrete definition classes that
inherit from those found in neighborly.defs.base_types. These definitions are loaded
into ever Neighborly instance when it is constructed.

"""

from __future__ import annotations

import random
from typing import Callable, ClassVar, Optional

from neighborly.components.business import Business, JobRole, OpenToPublic
from neighborly.components.character import Character, LifeStage, Sex, Species
from neighborly.components.location import (
    FrequentedBy,
    FrequentedLocations,
    LocationPreferences,
)
from neighborly.components.relationship import Relationships, SocialRules
from neighborly.components.residence import ResidentialBuilding, ResidentialUnit, Vacant
from neighborly.components.settlement import District, Settlement
from neighborly.components.skills import Skill, Skills
from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    BusinessSpawnTableEntry,
    CharacterSpawnTable,
    CharacterSpawnTableEntry,
    ResidenceSpawnTable,
    ResidenceSpawnTableEntry,
)
from neighborly.components.stats import Stat, Stats
from neighborly.components.traits import Trait, Traits
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
    TraitDef,
)
from neighborly.ecs import GameObject, World
from neighborly.helpers.settlement import create_district
from neighborly.helpers.skills import add_skill
from neighborly.helpers.stats import add_stat
from neighborly.helpers.traits import add_trait
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    EffectLibrary,
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
        skill = world.gameobject_manager.spawn_gameobject(name=self.display_name)
        tracery = skill.world.resource_manager.get_resource(Tracery)
        skill.add_component(
            Skill(
                definition_id=self.definition_id,
                display_name=tracery.generate(self.display_name),
                description=tracery.generate(self.description),
            )
        )
        return skill


class DefaultTraitDef(TraitDef):
    """A definition for a trait type."""

    def instantiate(self, world: World) -> GameObject:
        trait = world.gameobject_manager.spawn_gameobject(name=self.display_name)

        effect_library = trait.world.resource_manager.get_resource(EffectLibrary)
        tracery = trait.world.resource_manager.get_resource(Tracery)

        effects = [
            effect_library.create_from_obj(trait.world, entry) for entry in self.effects
        ]

        trait.add_component(
            Trait(
                definition_id=self.definition_id,
                display_name=tracery.generate(self.display_name),
                description=tracery.generate(self.description),
                effects=effects,
                conflicting_traits=self.conflicts_with,
            )
        )

        return trait


class DefaultSpeciesDef(DefaultTraitDef):
    """A definition for a trait type."""

    adolescent_age: int
    """Age this species reaches adolescence."""
    young_adult_age: int
    """Age this species reaches young adulthood."""
    adult_age: int
    """Age this species reaches main adulthood."""
    senior_age: int
    """Age this species becomes a senior/elder."""
    lifespan: int
    """The number of years that this species lives."""
    can_physically_age: bool
    """Does this character go through the various life stages."""

    def instantiate(self, world: World) -> GameObject:
        trait = super().instantiate(world)

        trait.add_component(
            Species(
                adolescent_age=self.adolescent_age,
                young_adult_age=self.young_adult_age,
                adult_age=self.adult_age,
                senior_age=self.senior_age,
                lifespan=self.lifespan,
                can_physically_age=self.can_physically_age,
            )
        )

        return trait


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
                name=name,
                description=self.description,
                settlement=settlement,
                residential_slots=self.residential_slots,
                business_slots=self.business_slots,
            )
        )
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

        district.add_component(BusinessSpawnTable(entries=table_entries))

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

        district.add_component(CharacterSpawnTable(entries=table_entries))

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

        district.add_component(ResidenceSpawnTable(entries=table_entries))


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

        if self.display_name:
            name = self.display_name

        elif self.name_factory:
            name = self.name_factories[self.name_factory](world, options)

        settlement.add_component(Settlement(name=name))
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

        building = residence.add_component(ResidentialBuilding(district=district))
        residence.add_component(Traits())
        residence.add_component(Stats())

        residence.name = self.display_name

        for _ in range(self.residential_units):
            residential_unit = world.gameobject_manager.spawn_gameobject(
                components=[Traits()], name="ResidentialUnit"
            )
            residence.add_child(residential_unit)
            residential_unit.add_component(
                ResidentialUnit(building=residence, district=district)
            )
            building.add_residential_unit(residential_unit)
            residential_unit.add_component(Vacant())

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

    def instantiate(
        self,
        world: World,
        options: CharacterGenOptions,
    ) -> GameObject:

        character = world.gameobject_manager.spawn_gameobject()
        character.metadata["definition_id"] = self.definition_id

        rng = world.resource_manager.get_resource(random.Random)

        library = character.world.resource_manager.get_resource(TraitLibrary)
        species = library.get_trait(self.species)

        character.add_component(
            Character(
                first_name="",
                last_name="",
                sex=rng.choice((Sex.MALE, Sex.FEMALE)),
                species=species,
            )
        )
        character.add_component(Traits())
        character.add_component(Skills())
        character.add_component(Stats())
        character.add_component(FrequentedLocations())
        character.add_component(Relationships())
        character.add_component(LocationPreferences())
        character.add_component(SocialRules())
        character.add_component(PersonalEventHistory())

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
        species = character.get_component(Character).species.get_component(Species)

        if options.life_stage is not "":

            life_stage: Optional[LifeStage] = LifeStage[options.life_stage]

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

    def initialize_traits(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Set the traits for a character."""
        character.add_component(Traits())
        rng = character.world.resource_manager.get_resource(random.Random)
        trait_library = character.world.resource_manager.get_resource(TraitLibrary)

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

        # By adding any stats from the definition
        for entry in self.stats:
            base_value = 0
            if entry.value is not None:
                base_value = entry.value
            elif entry.value_range:
                min_value, max_value = (
                    int(x.strip()) for x in entry.value_range.split("-")
                )
                base_value = rng.randint(min_value, max_value)

            add_stat(
                character,
                entry.stat,
                Stat(base_value=base_value, bounds=(entry.min_value, entry.max_value)),
            )

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
        role = world.gameobject_manager.spawn_gameobject(name=self.display_name)

        effects_library = world.resource_manager.get_resource(EffectLibrary)

        effect_instances = [
            effects_library.create_from_obj(world, entry) for entry in self.effects
        ]

        monthly_effect_instances = [
            effects_library.create_from_obj(world, entry)
            for entry in self.monthly_effects
        ]

        role.add_component(
            JobRole(
                definition_id=self.definition_id,
                display_name=self.display_name,
                description=self.description,
                job_level=self.job_level,
                requirements=[],
                effects=effect_instances,
                monthly_effects=monthly_effect_instances,
            )
        )

        return role


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
                name="",
                owner_role=job_role_library.get_role(self.owner_role).get_component(
                    JobRole
                ),
                employee_roles={
                    job_role_library.get_role(role).get_component(JobRole): count
                    for role, count in self.employee_roles.items()  # pylint: disable=E1101
                },
                district=district,
            )
        )

        business.add_component(Traits())
        business.add_component(FrequentedBy())
        business.add_component(PersonalEventHistory())
        business.add_component(Stats())
        business.add_component(Relationships())
        business.add_component(SocialRules())

        self.initialize_name(business, options)

        if self.open_to_public:
            business.add_component(OpenToPublic())

        for trait in self.traits:
            add_trait(business, trait)

        return business

    def initialize_name(
        self, business: GameObject, options: BusinessGenOptions
    ) -> None:
        """Generates a name for the business."""
        if options.name:
            business.get_component(Business).name = options.name

        elif self.name:
            business.get_component(Business).name = options.name

        elif self.name_factory:
            name = self.name_factories[self.name_factory](business.world, options)
            business.get_component(Business).name = name
