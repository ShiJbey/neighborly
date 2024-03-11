"""Default Content Definitions.

This module contains default implementations of concrete definition classes that
inherit from those found in neighborly.defs.base_types. These definitions are loaded
into ever Neighborly instance when it is constructed.

"""

from __future__ import annotations

import random
from typing import Any, Optional

from neighborly.components.business import Business, JobRole, OpenToPublic
from neighborly.components.character import Character, LifeStage, Sex, Species
from neighborly.components.location import FrequentedBy, FrequentedLocations
from neighborly.components.relationship import Relationships
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
    BusinessGenerationOptions,
    CharacterDef,
    CharacterGenerationOptions,
    DistrictDef,
    DistrictGenerationOptions,
    JobRoleDef,
    ResidenceDef,
    SettlementDef,
    SettlementGenerationOptions,
    SkillDef,
    TraitDef,
)
from neighborly.ecs import GameObject
from neighborly.helpers.settlement import create_district
from neighborly.helpers.skills import add_skill
from neighborly.helpers.stats import add_stat, get_stat
from neighborly.helpers.traits import add_trait
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    JobRoleLibrary,
    ResidenceLibrary,
    SettlementLibrary,
    SkillLibrary,
    TraitLibrary,
)
from neighborly.life_event import PersonalEventHistory
from neighborly.simulation import Simulation
from neighborly.tracery import Tracery


class DefaultSkillDef(SkillDef):
    """The default implementation of a skill definition."""

    def initialize(self, skill: GameObject) -> None:
        skill.add_component(
            Skill(
                definition_id=self.definition_id,
                display_name=self.display_name,
                description=self.description,
            )
        )


class DefaultTraitDef(TraitDef):
    """A definition for a trait type."""

    def initialize(self, trait: GameObject) -> None:
        trait.add_component(
            Trait(
                definition_id=self.definition_id,
                display_name=self.display_name,
                description=self.description,
                stat_modifiers=self.stat_modifiers,
                skill_modifiers=self.skill_modifiers,
                conflicting_traits=self.conflicts_with,
            )
        )


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

    def initialize(self, trait: GameObject) -> None:
        super().initialize(trait)

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


class DefaultDistrictDef(DistrictDef):
    """A definition for a district type specified by the user."""

    def initialize(
        self,
        settlement: GameObject,
        district: GameObject,
        options: DistrictGenerationOptions,
    ) -> None:
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
        self.initialize_business_spawn_table(district)
        self.initialize_character_spawn_table(district)
        self.initialize_residence_spawn_table(district)

    def initialize_name(self, district: GameObject) -> None:
        """Generates a name for the district."""
        tracery = district.world.resources.get_resource(Tracery)
        name = tracery.generate(self.display_name)
        district.get_component(District).name = name
        district.name = name

    def initialize_business_spawn_table(self, district: GameObject) -> None:
        """Create the business spawn table for the district."""
        world = district.world

        business_library = world.resources.get_resource(BusinessLibrary)

        table_entries: list[BusinessSpawnTableEntry] = []

        for entry in self.businesses:
            if isinstance(entry, str):
                business_def = business_library.get_definition(entry)
                table_entries.append(
                    BusinessSpawnTableEntry(
                        name=entry,
                        spawn_frequency=business_def.spawn_frequency,
                        max_instances=business_def.max_instances,
                        min_population=business_def.min_population,
                        instances=0,
                    )
                )
            else:
                business_def = business_library.get_definition(entry["definition_id"])

                table_entries.append(
                    BusinessSpawnTableEntry(
                        name=entry["definition_id"],
                        spawn_frequency=entry.get(
                            "spawn_frequency", business_def.spawn_frequency
                        ),
                        max_instances=entry.get(
                            "max_instances", business_def.max_instances
                        ),
                        min_population=entry.get(
                            "min_population", business_def.min_population
                        ),
                        instances=0,
                    )
                )

        district.add_component(BusinessSpawnTable(entries=table_entries))

    def initialize_character_spawn_table(self, district: GameObject) -> None:
        """Create the character spawn table for the district."""
        world = district.world
        character_library = world.resources.get_resource(CharacterLibrary)

        table_entries: list[CharacterSpawnTableEntry] = []

        for entry in self.characters:

            character_def = character_library.get_definition(entry["definition_id"])

            table_entries.append(
                CharacterSpawnTableEntry(
                    name=entry["definition_id"],
                    spawn_frequency=entry.get(
                        "spawn_frequency", character_def.spawn_frequency
                    ),
                )
            )

        district.add_component(CharacterSpawnTable(entries=table_entries))

    def initialize_residence_spawn_table(self, district: GameObject) -> None:
        """Create the residence spawn table for the district."""
        world = district.world
        residence_library = world.resources.get_resource(ResidenceLibrary)

        table_entries: list[ResidenceSpawnTableEntry] = []

        for entry in self.residences:
            # The entry is a string. We import all defaults from the main definition
            if isinstance(entry, str):
                residence_def = residence_library.get_definition(entry)
                table_entries.append(
                    ResidenceSpawnTableEntry(
                        name=entry,
                        spawn_frequency=residence_def.spawn_frequency,
                        instances=0,
                        required_population=residence_def.required_population,
                        max_instances=residence_def.max_instances,
                        is_multifamily=residence_def.is_multifamily,
                    )
                )

            # The entry is an object with overrides
            else:
                residence_def = residence_library.get_definition(entry["definition_id"])

                table_entries.append(
                    ResidenceSpawnTableEntry(
                        name=entry["definition_id"],
                        spawn_frequency=entry.get(
                            "spawn_frequency", residence_def.spawn_frequency
                        ),
                        instances=0,
                        required_population=entry.get(
                            "required_population", residence_def.required_population
                        ),
                        max_instances=entry.get(
                            "max_instances", residence_def.max_instances
                        ),
                        is_multifamily=residence_def.is_multifamily,
                    )
                )

        district.add_component(ResidenceSpawnTable(entries=table_entries))


class DefaultSettlementDef(SettlementDef):
    """A definition for a settlement type specified by the user."""

    def initialize(
        self, settlement: GameObject, options: SettlementGenerationOptions
    ) -> None:
        settlement.metadata["definition_id"] = self.definition_id
        self.initialize_name(settlement)
        self.initialize_districts(settlement)

    def initialize_name(self, settlement: GameObject) -> None:
        """Generates a name for the settlement."""
        tracery = settlement.world.resources.get_resource(Tracery)
        settlement_name = tracery.generate(self.display_name)
        settlement.get_component(Settlement).name = settlement_name
        settlement.name = settlement_name

    def initialize_districts(self, settlement: GameObject) -> None:
        """Instantiates the settlement's districts."""

        # loop through a list of dictionary entry in self.districts, entry is settlement def strictint entry, entry go through ifs
        # if entry.id: if an id exists
        # elif entry.tags: Go through the tags
        # else: raise Error("Must specify tags or id")

        library = settlement.world.resources.get_resource(DistrictLibrary)
        rng = settlement.world.resources.get_resource(random.Random)

        for district_entry in self.districts:
            if district_entry.defintion_id:
                district = create_district(
                    settlement.world, settlement, district_entry.defintion_id
                )
                settlement.add_child(district)
            elif district_entry.tags:
                matching_districts = library.get_definition_with_tags(
                    district_entry.tags
                )

                if matching_districts:
                    chosen_district = rng.choice(matching_districts)
                    district = create_district(
                        settlement.world, settlement, chosen_district.definition_id
                    )
                    settlement.add_child(district)

            else:
                raise ValueError("Must specify tags or id")

        # for definition_id in self.districts:
        #     district = create_district(settlement.world, settlement, definition_id)
        #     settlement.add_child(district)
        # Old version


class DefaultResidenceDef(ResidenceDef):
    """A default implementation of a Residence Definition."""

    @property
    def is_multifamily(self) -> bool:
        """Is this a multifamily residential building"""
        return self.residential_units > 1

    def initialize(self, district: GameObject, residence: GameObject) -> None:
        world = residence.world

        building = ResidentialBuilding(district=district)
        residence.add_component(building)
        residence.add_component(Traits())
        residence.add_component(Stats())

        residence.name = self.display_name

        for _ in range(self.residential_units):
            residential_unit = world.gameobjects.spawn_gameobject(
                components=[Traits()], name="ResidentialUnit"
            )
            residence.add_child(residential_unit)
            residential_unit.add_component(
                ResidentialUnit(building=residence, district=district)
            )
            building.add_residential_unit(residential_unit)
            residential_unit.add_component(Vacant())


class DefaultCharacterDef(CharacterDef):
    """Default implementation for character definitions."""

    def initialize(
        self, character: GameObject, options: CharacterGenerationOptions
    ) -> None:
        rng = character.world.resources.get_resource(random.Random)

        species_id = rng.choice(self.species)

        library = character.world.resources.get_resource(TraitLibrary)
        species = library.get_trait(species_id)

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
        character.add_component(PersonalEventHistory())

        self.initialize_name(character, options)
        self.initialize_character_age(character, options)
        self.initialize_character_stats(character, options)
        self.initialize_traits(character, options)
        self.initialize_character_skills(character)

    def initialize_name(
        self, character: GameObject, options: CharacterGenerationOptions
    ) -> None:
        """Initialize the character's name.

        Parameters
        ----------
        character
            The character to initialize.
        """
        default_first_name: str = kwargs.get("first_name", "")
        default_last_name: str = kwargs.get("last_name", "")

        character_comp = character.get_component(Character)

        character_comp.first_name = self.generate_first_name(
            character, default_first_name
        )
        character_comp.last_name = self.generate_last_name(character, default_last_name)

    def initialize_character_age(
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

    def initialize_traits(
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

    def initialize_character_stats(
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

    def initialize_character_skills(self, character: GameObject) -> None:
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


class DefaultJobRoleDef(JobRoleDef):
    """A default implementation of a Job Role Definition."""

    def initialize(self, role: GameObject, **kwargs: Any) -> None:
        role.add_component(
            JobRole(
                definition_id=self.definition_id,
                display_name=self.display_name,
                description=self.description,
                job_level=self.job_level,
                requirements=self.requirements,
                stat_modifiers=self.stat_modifiers,
                periodic_stat_boosts=self.periodic_stat_boosts,
                periodic_skill_boosts=self.periodic_skill_boosts,
            )
        )


class DefaultBusinessDef(BusinessDef):
    """A default implementation of a Business Definition."""

    def initialize(
        self,
        district: GameObject,
        business: GameObject,
        options: BusinessGenerationOptions,
    ) -> None:
        world = business.world
        job_role_library = world.resources.get_resource(JobRoleLibrary)

        business.add_component(
            Business(
                name="",
                owner_role=job_role_library.get_role(self.owner_role).get_component(
                    JobRole
                ),
                employee_roles={
                    job_role_library.get_role(role).get_component(JobRole): count
                    for role, count in self.employee_roles.items()
                },
                district=district,
            )
        )

        business.add_component(Traits())
        business.add_component(FrequentedBy())
        business.add_component(PersonalEventHistory())
        business.add_component(Stats())
        business.add_component(Relationships())

        self.initialize_name(business)

        if self.open_to_public:
            business.add_component(OpenToPublic())

        for trait in self.traits:
            add_trait(business, trait)

    def initialize_name(self, business: GameObject) -> None:
        """Generates a name for the business."""
        tracery = business.world.resources.get_resource(Tracery)
        name = tracery.generate(self.display_name)
        business.get_component(Business).name = name
        business.name = name


def load_plugin(sim: Simulation) -> None:
    """Load plugin content."""

    sim.world.resources.get_resource(TraitLibrary).add_definition_type(
        DefaultTraitDef, set_default=True
    )

    sim.world.resources.get_resource(SkillLibrary).add_definition_type(
        DefaultSkillDef, set_default=True
    )

    sim.world.resources.get_resource(TraitLibrary).add_definition_type(
        DefaultSpeciesDef
    )

    sim.world.resources.get_resource(DistrictLibrary).add_definition_type(
        DefaultDistrictDef, set_default=True
    )

    sim.world.resources.get_resource(SettlementLibrary).add_definition_type(
        DefaultSettlementDef, set_default=True
    )

    sim.world.resources.get_resource(ResidenceLibrary).add_definition_type(
        DefaultResidenceDef, set_default=True
    )

    sim.world.resources.get_resource(CharacterLibrary).add_definition_type(
        DefaultCharacterDef, set_default=True
    )

    sim.world.resources.get_resource(JobRoleLibrary).add_definition_type(
        DefaultJobRoleDef, set_default=True
    )

    sim.world.resources.get_resource(BusinessLibrary).add_definition_type(
        DefaultBusinessDef, set_default=True
    )
