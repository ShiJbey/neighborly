"""Default Content Definitions.

This module contains default implementations of concrete definition classes that
inherit from those found in neighborly.defs.base_types. These definitions are loaded
into ever Neighborly instance when it is constructed.

"""

from __future__ import annotations

import random
from typing import Callable, ClassVar, Optional

from neighborly.components.character import Character, LifeStage
from neighborly.components.location import Location
from neighborly.components.residence import ResidentialBuilding, ResidentialUnit, Vacant
from neighborly.components.settlement import District
from neighborly.components.shared import Age
from neighborly.components.traits import Traits
from neighborly.defs.base_types import (
    BusinessDef,
    BusinessGenOptions,
    CharacterDef,
    CharacterGenOptions,
    DistrictDef,
    DistrictGenOptions,
    ResidenceDef,
    ResidenceGenOptions,
    SettlementDef,
    SettlementGenOptions,
)
from neighborly.ecs import GameObject, World
from neighborly.helpers.character import set_species
from neighborly.helpers.settlement import create_district
from neighborly.helpers.stats import add_stat, get_stat, has_stat
from neighborly.helpers.traits import add_trait
from neighborly.libraries import DistrictLibrary, DistrictNameFactories, TraitLibrary
from neighborly.tracery import Tracery

STAT_MAX_VALUE: int = 100


def default_district_name_factory(world: World, options: DistrictGenOptions) -> str:
    """Generate a new name"""
    tracery = world.resource_manager.get_resource(Tracery)
    name = tracery.generate("#settlement_name#")
    return name


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

        name = ""

        if self.name:
            name = self.name
        elif self.name_factory:
            factories = world.resource_manager.get_resource(DistrictNameFactories)
            name = factories.get_factory(self.name_factory)(world, options)

        district.add_component(
            District(
                gameobject=district,
                name=name,
                description=self.description,
                residential_slots=self.residential_slots,
                business_slots=self.business_slots,
            )
        )

        for (
            component_name,
            component_args,
        ) in self.components.items():  # pylint: disable=E1101
            component = world.gameobjects.component_factories[
                component_name
            ].instantiate(district, **component_args)

            district.add_component(component)

        return district


def default_settlement_name_factory(world: World, options: SettlementGenOptions) -> str:
    """Generate a new name"""
    tracery = world.resource_manager.get_resource(Tracery)
    name = tracery.generate("#settlement_name#")
    return name


class DefaultSettlementDef(SettlementDef):
    """A definition for a settlement type specified by the user."""

    def instantiate(self, world: World, options: SettlementGenOptions) -> GameObject:
        settlement = world.gameobject_manager.spawn_gameobject()
        settlement.metadata["definition_id"] = self.definition_id

        for (
            component_name,
            component_args,
        ) in self.components.items():  # pylint: disable=E1101
            component = world.gameobjects.component_factories[
                component_name
            ].instantiate(settlement, **component_args)

            settlement.add_component(component)

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
                    district.get_component(District).settlement = settlement
                    settlement.add_child(district)


class DefaultResidenceDef(ResidenceDef):
    """A default implementation of a Residence Definition."""

    def instantiate(
        self, world: World, district: GameObject, options: ResidenceGenOptions
    ) -> GameObject:

        residence = world.gameobject_manager.spawn_gameobject()
        residence.metadata["definition_id"] = self.definition_id

        world = residence.world

        for (
            component_name,
            component_args,
        ) in self.components.items():  # pylint: disable=E1101
            component = world.gameobjects.component_factories[
                component_name
            ].instantiate(residence, **component_args)

            residence.add_component(component)

        building = residence.get_component(ResidentialBuilding)

        for _ in range(self.residential_units):
            residential_unit = world.gameobject_manager.spawn_gameobject(
                name="ResidentialUnit"
            )
            residential_unit.add_component(Traits(residential_unit))
            residence.add_child(residential_unit)
            residential_unit.add_component(
                ResidentialUnit(residential_unit, building=residence)
            )
            residential_unit.add_component(Location(residential_unit, is_private=True))
            building.add_residential_unit(residential_unit)
            residential_unit.add_component(Vacant(residential_unit))

        return residence


def generate_any_first_name(world: World, options: CharacterGenOptions) -> str:
    """Generate a first name for a character"""

    tracery = world.resource_manager.get_resource(Tracery)
    rng = world.resource_manager.get_resource(random.Random)

    pattern = rng.choice(["#first_name::feminine#", "#first_name::masculine#"])

    name = tracery.generate(pattern)

    return name


def generate_masculine_first_name(world: World, options: CharacterGenOptions) -> str:
    """Generate a masculine first name for a character"""

    tracery = world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#first_name::masculine#")

    return name


def generate_feminine_first_name(world: World, options: CharacterGenOptions) -> str:
    """Generate a feminine first name for a character"""

    tracery = world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#first_name::feminine#")

    return name


def generate_last_name(world: World, options: CharacterGenOptions) -> str:
    """Generate a last_name for a character."""

    tracery = world.resource_manager.get_resource(Tracery)

    name = tracery.generate("#last_name#")

    return name


class DefaultCharacterDef(CharacterDef):
    """Default implementation for character definitions."""

    def instantiate(
        self,
        world: World,
        options: CharacterGenOptions,
    ) -> GameObject:

        character = world.gameobject_manager.spawn_gameobject()
        character.metadata["definition_id"] = self.definition_id

        for (
            component_name,
            component_args,
        ) in self.components.items():  # pylint: disable=E1101
            component = world.gameobjects.component_factories[
                component_name
            ].instantiate(character, **component_args)

            character.add_component(component)

        self.initialize_character_age(character, options)
        self.initialize_character_stats(character)
        self.initialize_traits(character, options)

        return character

    def initialize_character_age(
        self, character: GameObject, options: CharacterGenOptions
    ) -> None:
        """Initializes the characters age."""
        rng = character.world.resource_manager.get_resource(random.Random)

        character_comp = character.get_component(Character)
        age = character.get_component(Age)
        species = character.get_component(Character).species

        if options.life_stage:

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
            base_value=float(rng.uniform(0, STAT_MAX_VALUE)),
            bounds=(0, STAT_MAX_VALUE),
        )

        add_stat(
            character,
            "kindness",
            base_value=float(rng.randint(0, STAT_MAX_VALUE)),
            bounds=(0, STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "courage",
            base_value=float(rng.randint(0, STAT_MAX_VALUE)),
            bounds=(0, STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "stewardship",
            base_value=float(rng.randint(0, STAT_MAX_VALUE)),
            bounds=(0, STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "sociability",
            base_value=float(rng.randint(0, STAT_MAX_VALUE)),
            bounds=(0, STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "intelligence",
            base_value=float(rng.randint(0, STAT_MAX_VALUE)),
            bounds=(0, STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "discipline",
            base_value=float(rng.randint(0, STAT_MAX_VALUE)),
            bounds=(0, STAT_MAX_VALUE),
            is_discrete=True,
        )

        add_stat(
            character,
            "charm",
            base_value=float(rng.randint(0, STAT_MAX_VALUE)),
            bounds=(0, STAT_MAX_VALUE),
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


class DefaultBusinessDef(BusinessDef):
    """A default implementation of a Business Definition."""

    name_factories: ClassVar[dict[str, Callable[[World, BusinessGenOptions], str]]] = {}

    def instantiate(
        self, world: World, district: GameObject, options: BusinessGenOptions
    ) -> GameObject:

        business = world.gameobject_manager.spawn_gameobject()
        business.metadata["definition_id"] = self.definition_id

        for (
            component_name,
            component_args,
        ) in self.components.items():  # pylint: disable=E1101
            component = world.gameobjects.component_factories[
                component_name
            ].instantiate(business, **component_args)

            business.add_component(component)

        # Initialize the life span
        rng = world.resource_manager.get_resource(random.Random)
        min_value, max_value = (int(x.strip()) for x in self.lifespan.split("-"))
        base_lifespan = rng.randint(min_value, max_value)
        add_stat(business, "lifespan", base_value=base_lifespan, is_discrete=True)

        for trait in self.traits:
            add_trait(business, trait)

        return business
