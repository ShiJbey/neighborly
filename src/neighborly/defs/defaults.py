"""Default Content Definitions.

This module contains default implementations of concrete definition classes that
inherit from those found in neighborly.defs.base_types. These definitions are loaded
into ever Neighborly instance when it is constructed.

"""

from __future__ import annotations

import random
from typing import Optional

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
from neighborly.helpers.stats import add_stat
from neighborly.helpers.traits import add_trait
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    EffectLibrary,
    JobRoleLibrary,
    ResidenceLibrary,
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


class DefaultDistrictDef(DistrictDef):
    """A definition for a district type specified by the user."""

    def instantiate(
        self,
        world: World,
        settlement: GameObject,
        options: DistrictGenOptions,
    ) -> GameObject:
        district = world.gameobject_manager.spawn_gameobject()
        district.metadata["definition_id"] = self.definition_id

        district.add_component(
            District(
                name="",
                description="",
                settlement=settlement,
                residential_slots=self.residential_slots,
                business_slots=self.business_slots,
            )
        )

        self.initialize_name(district)
        self.initialize_description(district)
        self.initialize_business_spawn_table(district)
        self.initialize_character_spawn_table(district)
        self.initialize_residence_spawn_table(district)

        return district

    def initialize_name(self, district: GameObject) -> None:
        """Generates a name for the district."""
        tracery = district.world.resource_manager.get_resource(Tracery)
        name = tracery.generate(self.display_name)
        district.get_component(District).name = name
        district.name = name

    def initialize_description(self, district: GameObject) -> None:
        """Generates a description for the district."""
        tracery = district.world.resource_manager.get_resource(Tracery)
        description = tracery.generate(self.description)
        district.get_component(District).description = description

    def initialize_business_spawn_table(self, district: GameObject) -> None:
        """Create the business spawn table for the district."""
        world = district.world
        rng = world.resource_manager.get_resource(random.Random)
        business_library = world.resource_manager.get_resource(BusinessLibrary)

        table_entries: list[BusinessSpawnTableEntry] = []

        for entry in self.businesses:
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

        for entry in self.characters:
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

        for entry in self.residences:
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


class DefaultSettlementDef(SettlementDef):
    """A definition for a settlement type specified by the user."""

    def instantiate(self, world: World, options: SettlementGenOptions) -> GameObject:
        settlement = world.gameobject_manager.spawn_gameobject()
        settlement.metadata["definition_id"] = self.definition_id
        settlement.add_component(Settlement(name=""))
        self.initialize_name(settlement)
        self.initialize_districts(settlement)
        return settlement

    def initialize_name(self, settlement: GameObject) -> None:
        """Generates a name for the settlement."""
        tracery = settlement.world.resource_manager.get_resource(Tracery)
        settlement_name = tracery.generate(self.display_name)
        settlement.get_component(Settlement).name = settlement_name
        settlement.name = settlement_name

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


class DefaultCharacterDef(CharacterDef):
    """Default implementation for character definitions."""

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

        self.initialize_name(
            character, first_name=options.first_name, last_name=options.last_name
        )
        self.initialize_character_age(character, options)
        self.initialize_character_stats(character)
        self.initialize_traits(character, options)
        self.initialize_character_skills(character)

        return character

    def initialize_name(
        self,
        character: GameObject,
        first_name: str = "#first_name#",
        last_name: str = "#last_name#",
    ) -> None:
        """Initialize the character's name.

        Parameters
        ----------
        character
            The character to initialize.
        """
        character_comp = character.get_component(Character)

        character_comp.first_name = self.generate_first_name(character, first_name)
        character_comp.last_name = self.generate_last_name(character, last_name)

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

        traits: list[str] = []
        trait_weights: list[int] = []

        for trait_id in trait_library.trait_ids:
            trait_def = trait_library.get_definition(trait_id)
            if trait_def.spawn_frequency >= 1:
                traits.append(trait_id)
                trait_weights.append(trait_def.spawn_frequency)

        if len(traits) == 0:
            return

        max_traits = options.n_traits

        chosen_traits = rng.choices(traits, trait_weights, k=max_traits)

        for trait in chosen_traits:
            add_trait(character, trait)

        for trait in options.traits:
            add_trait(character, trait)

    def initialize_character_stats(self, character: GameObject) -> None:
        """Initializes a characters stats with random values."""
        rng = character.world.resource_manager.get_resource(random.Random)

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
        # rng = character.world.resource_manager.get_resource(random.Random)
        # for entry in self.skills:

        #     value = rng.randint(interval[0], interval[1])
        #     add_skill(character, entry., value)

    @staticmethod
    def generate_first_name(character: GameObject, pattern: str) -> str:
        """Generates a first name for the character"""

        tracery = character.world.resource_manager.get_resource(Tracery)

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

        tracery = character.world.resource_manager.get_resource(Tracery)

        if pattern:
            name = tracery.generate(pattern)
        else:
            name = tracery.generate("#last_name#")

        return name


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

        self.initialize_name(business)

        if self.open_to_public:
            business.add_component(OpenToPublic())

        for trait in self.traits:
            add_trait(business, trait)

        return business

    def initialize_name(self, business: GameObject) -> None:
        """Generates a name for the business."""
        tracery = business.world.resource_manager.get_resource(Tracery)
        name = tracery.generate(self.display_name)
        business.get_component(Business).name = name
        business.name = name
