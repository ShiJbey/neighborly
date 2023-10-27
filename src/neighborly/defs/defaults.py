"""Default Content Definitions.

This module contains default implementations of concrete definition classes that
inherit from those found in neighborly.defs.base_types.

"""

from __future__ import annotations

import random
from typing import Any, Optional, Union

import attrs

from neighborly.components.business import Business, JobRole
from neighborly.components.character import Character, LifeStage, Sex, Species
from neighborly.components.location import (
    FrequentedBy,
    FrequentedLocations,
    LocationPreferences,
)
from neighborly.components.relationship import Relationships, SocialRules
from neighborly.components.residence import Residence, ResidentialBuilding, Vacant
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
    CharacterDef,
    DistrictDef,
    JobRoleDef,
    ResidenceDef,
    SettlementDef,
    SkillDef,
    TraitDef,
)
from neighborly.ecs import GameObject
from neighborly.helpers.settlement import create_district
from neighborly.helpers.stats import add_stat, get_stat
from neighborly.helpers.traits import add_trait
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    EffectLibrary,
    JobRoleLibrary,
    ResidenceLibrary,
    TraitLibrary,
)
from neighborly.life_event import PersonalEventHistory
from neighborly.tracery import Tracery


@attrs.define
class DefaultSkillDef(SkillDef):
    """A definition for a skill type."""

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> SkillDef:
        definition_id = obj["definition_id"]
        display_name = obj.get("display_name", definition_id)
        description = obj.get("description", "")

        return cls(
            definition_id=definition_id,
            display_name=display_name,
            description=description,
        )

    def initialize(self, skill: GameObject) -> None:
        tracery = skill.world.resource_manager.get_resource(Tracery)
        skill.add_component(
            Skill(
                definition_id=self.definition_id,
                display_name=tracery.generate(self.display_name),
                description=tracery.generate(self.description),
            )
        )


@attrs.define
class DefaultTraitDef(TraitDef):
    """A definition for a trait type."""

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> TraitDef:
        """Create a trait definition from a data dictionary."""

        definition_id: str = obj["definition_id"]
        display_name: str = obj.get("display_name", definition_id)
        description: str = obj.get("description", "")
        effects: list[dict[str, Any]] = obj.get("effects", [])
        conflicts_with: list[str] = obj.get("conflicts_with", [])
        spawn_frequency: int = obj.get("spawn_frequency", 0)
        inheritance_chance_single: float = float(
            obj.get("inheritance_chance_single", 0)
        )
        inheritance_chance_both: float = float(obj.get("inheritance_chance_both", 0))

        return cls(
            definition_id=definition_id,
            display_name=display_name,
            description=description,
            effects=effects,
            conflicts_with=frozenset(conflicts_with),
            spawn_frequency=spawn_frequency,
            inheritance_chance_single=inheritance_chance_single,
            inheritance_chance_both=inheritance_chance_both,
        )

    def initialize(self, trait: GameObject) -> None:
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


@attrs.define(kw_only=True)
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

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> TraitDef:
        """Create a trait definition from a data dictionary."""

        definition_id: str = obj["definition_id"]
        display_name: str = obj.get("display_name", definition_id)
        description: str = obj.get("description", "")
        effects: list[dict[str, Any]] = obj.get("effects", [])
        conflicts_with: list[str] = obj.get("conflicts_with", [])
        adolescent_age = obj["adolescent_age"]
        young_adult_age = obj["young_adult_age"]
        adult_age = obj["adult_age"]
        senior_age = obj["senior_age"]
        lifespan = obj["lifespan"]
        can_physically_age: bool = obj.get("can_physically_age", True)

        return cls(
            definition_id=definition_id,
            display_name=display_name,
            description=description,
            effects=effects,
            conflicts_with=frozenset(conflicts_with),
            spawn_frequency=0,
            inheritance_chance_single=0,
            inheritance_chance_both=0,
            adolescent_age=adolescent_age,
            young_adult_age=young_adult_age,
            adult_age=adult_age,
            senior_age=senior_age,
            lifespan=lifespan,
            can_physically_age=can_physically_age,
        )

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


@attrs.define
class DefaultDistrictDef(DistrictDef):
    """A definition for a district type specified by the user."""

    def initialize(self, settlement: GameObject, district: GameObject) -> None:
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

        business_library = world.resource_manager.get_resource(BusinessLibrary)

        table_entries: list[BusinessSpawnTableEntry] = []

        for entry in self.business_types:
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
        character_library = world.resource_manager.get_resource(CharacterLibrary)

        table_entries: list[CharacterSpawnTableEntry] = []

        for entry in self.character_types:
            if isinstance(entry, str):
                character_def = character_library.get_definition(entry)
                table_entries.append(
                    CharacterSpawnTableEntry(
                        name=entry,
                        spawn_frequency=character_def.spawn_frequency,
                    )
                )
            else:
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
        residence_library = world.resource_manager.get_resource(ResidenceLibrary)

        table_entries: list[ResidenceSpawnTableEntry] = []

        for entry in self.residence_types:
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

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> DistrictDef:
        """Create a district definition from a data dictionary."""
        definition_id: str = obj["definition_id"]
        display_name: str = obj.get("display_name", definition_id)
        description: str = obj.get("description", "")

        business_types_data: list[Union[str, dict[str, Any]]] = obj.get(
            "business_types", []
        )

        business_types: list[dict[str, Any]] = []
        for entry in business_types_data:
            if isinstance(entry, str):
                business_types.append({"definition_id": entry})
            else:
                business_types.append(entry)

        residence_types_data: list[Union[str, dict[str, Any]]] = obj.get(
            "residence_types", []
        )

        residence_types: list[dict[str, Any]] = []
        for entry in residence_types_data:
            if isinstance(entry, str):
                residence_types.append({"definition_id": entry})
            else:
                residence_types.append(entry)

        character_types_data: list[Union[str, dict[str, Any]]] = obj.get(
            "character_types", []
        )
        character_types: list[dict[str, Any]] = []
        for entry in character_types_data:
            if isinstance(entry, str):
                character_types.append({"definition_id": entry})
            else:
                character_types.append(entry)

        residential_slots = obj.get("residential_slots", 0)
        business_slots = obj.get("business_slots", 0)

        return cls(
            definition_id=definition_id,
            display_name=display_name,
            description=description,
            business_types=business_types,
            residence_types=residence_types,
            character_types=character_types,
            business_slots=business_slots,
            residential_slots=residential_slots,
        )


@attrs.define
class DefaultSettlementDef(SettlementDef):
    """A definition for a settlement type specified by the user."""

    def initialize(self, settlement: GameObject) -> None:
        settlement.metadata["definition_id"] = self.definition_id
        self.initialize_name(settlement)
        self.initialize_districts(settlement)

    def initialize_name(self, settlement: GameObject) -> None:
        """Generates a name for the settlement."""
        tracery = settlement.world.resource_manager.get_resource(Tracery)
        settlement_name = tracery.generate(self.display_name)
        settlement.get_component(Settlement).name = settlement_name
        settlement.name = settlement_name

    def initialize_districts(self, settlement: GameObject) -> None:
        """Instantiates the settlement's districts."""
        for definition_id in self.districts:
            district = create_district(settlement.world, settlement, definition_id)
            settlement.add_child(district)

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> SettlementDef:
        """Create a settlement definition from a data dictionary."""
        definition_id: str = obj["definition_id"]
        display_name: str = obj.get("display_name", definition_id)
        districts: list[str] = obj.get("districts", [])

        return cls(
            definition_id=definition_id,
            display_name=display_name,
            districts=districts,
        )


@attrs.define
class DefaultResidenceDef(ResidenceDef):
    """A default implementation of a Residence Definition."""

    @property
    def is_multifamily(self) -> bool:
        """Is this a multifamily residential building"""
        return self.residential_units > 1

    def initialize(self, district: GameObject, residence: GameObject) -> None:
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
            residential_unit.add_component(Residence(district=district))
            building.add_residential_unit(residential_unit)
            residential_unit.add_component(Vacant())

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> ResidenceDef:
        """Create a residence definition from a data dictionary."""
        definition_id: str = obj["definition_id"]
        display_name: str = obj["display_name"]
        spawn_frequency: int = obj.get("spawn_frequency", 1)
        residential_units: int = obj.get("residential_units", 1)
        required_population: int = obj.get("required_population", 0)
        max_instances: int = obj.get("max_instances", 9999)

        return cls(
            definition_id=definition_id,
            display_name=display_name,
            spawn_frequency=spawn_frequency,
            residential_units=residential_units,
            required_population=required_population,
            max_instances=max_instances,
        )


@attrs.define
class DefaultCharacterDef(CharacterDef):
    """Default implementation for character definitions."""

    def initialize(self, character: GameObject, **kwargs: Any) -> None:
        rng = character.world.resource_manager.get_resource(random.Random)

        species_id = rng.choice(self.species)

        library = character.world.resource_manager.get_resource(TraitLibrary)
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
        character.add_component(LocationPreferences())
        character.add_component(SocialRules())
        character.add_component(PersonalEventHistory())

        self.initialize_name(character, **kwargs)
        self.initialize_character_age(character, **kwargs)
        self.initialize_character_stats(character, **kwargs)
        self.initialize_traits(character, **kwargs)

    def initialize_name(self, character: GameObject, **kwargs: Any) -> None:
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

    def initialize_character_age(self, character: GameObject, **kwargs: Any) -> None:
        """Initializes the characters age."""
        rng = character.world.resource_manager.get_resource(random.Random)
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

    def initialize_traits(self, character: GameObject, **kwargs: Any) -> None:
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

        max_traits = kwargs.get("n_traits", self.max_traits)

        chosen_traits = rng.choices(traits, trait_weights, k=max_traits)

        for trait in chosen_traits:
            add_trait(character, trait)

        default_traits: list[str] = kwargs.get("default_traits", [])

        for trait in default_traits:
            add_trait(character, trait)

    def initialize_character_stats(self, character: GameObject, **kwargs: Any) -> None:
        """Initializes a characters stats with random values."""
        rng = character.world.resource_manager.get_resource(random.Random)

        character_comp = character.get_component(Character)
        species = character.get_component(Character).species.get_component(Species)

        health = add_stat(character, "health", Stat(base_value=100))
        health_decay = add_stat(
            character, "health_decay", Stat(base_value=100.0 / species.lifespan)
        )
        fertility = add_stat(
            character,
            "fertility",
            Stat(base_value=round(rng.random(), 2), bounds=(0, 1.0)),
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

    def initialize_character_skills(self, character: GameObject, **kwargs: Any) -> None:
        """Add default skills to the character."""
        raise NotImplementedError()

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

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> CharacterDef:
        """Create a character definition from a data dictionary."""
        definition_id: str = obj["definition_id"]
        spawn_frequency: int = obj.get("spawn_frequency", 1)
        max_traits: int = obj.get("max_traits", 3)
        species: list[str] = obj["species"]
        default_traits: list[str] = obj.get("default_traits", [])
        default_skills: list[dict[str, Any]] = obj.get("default_skills", [])

        return cls(
            definition_id=definition_id,
            spawn_frequency=spawn_frequency,
            max_traits=max_traits,
            default_skills=default_skills,
            default_traits=default_traits,
            species=species,
        )


@attrs.define
class DefaultJobRoleDef(JobRoleDef):
    """A default implementation of a Job Role Definition."""

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> JobRoleDef:
        """Create JobRoleDef from a data dictionary."""
        definition_id: str = obj["definition_id"]
        display_name: str = obj.get("display_name", definition_id)
        job_level: int = obj.get("job_level", 1)
        requirements_data: list[dict[str, Any]] = obj.get("requirements", [])
        effects_data: list[dict[str, Any]] = obj.get("../effects", [])
        monthly_effects_data: list[dict[str, Any]] = obj.get("monthly_effects", [])

        return cls(
            definition_id=definition_id,
            display_name=display_name,
            job_level=job_level,
            requirements=requirements_data,
            effects=effects_data,
            monthly_effects=monthly_effects_data,
        )

    def initialize(self, role: GameObject, **kwargs: Any) -> None:
        world = role.world

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
                name=self.display_name,
                job_level=self.job_level,
                requirements=[],
                effects=effect_instances,
                monthly_effects=monthly_effect_instances,
            )
        )


@attrs.define
class DefaultBusinessDef(BusinessDef):
    """A default implementation of a Business Definition."""

    def initialize(self, district: GameObject, business: GameObject) -> None:
        world = business.world
        job_role_library = world.resource_manager.get_resource(JobRoleLibrary)

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
        business.add_component(SocialRules())

        self.initialize_name(business)

        for trait in self.traits:
            add_trait(business, trait)

    def initialize_name(self, business: GameObject) -> None:
        """Generates a name for the business."""
        tracery = business.world.resource_manager.get_resource(Tracery)
        name = tracery.generate(self.display_name)
        business.get_component(Business).name = name
        business.name = name

    @classmethod
    def from_obj(cls, obj: dict[str, Any]) -> BusinessDef:
        """Create a business definition from a data dictionary."""
        definition_id: str = obj["definition_id"]
        spawn_frequency: int = obj.get("spawn_frequency", 1)
        display_name: str = obj.get("display_name", definition_id)
        min_population: int = obj.get("min_population", 0)
        max_instances: int = obj.get("max_instances", 9999)
        traits: list[str] = obj.get("traits", [])
        open_to_public: bool = obj.get("open_to_public", False)

        owner_role: str = obj["owner_role"]

        employee_roles: dict[str, int] = obj.get("employee_roles", {})

        return cls(
            definition_id=definition_id,
            spawn_frequency=spawn_frequency,
            display_name=display_name,
            min_population=min_population,
            max_instances=max_instances,
            owner_role=owner_role,
            employee_roles=employee_roles,
            traits=traits,
            open_to_public=open_to_public,
        )
