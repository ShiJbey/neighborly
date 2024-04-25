# pylint: disable=C0121

"""Built-in Systems.

This module contains built-in systems that help simulations function.

"""

from __future__ import annotations

import random
from typing import ClassVar, Optional

from sqlalchemy import select

from neighborly.components.beliefs import Belief
from neighborly.components.business import Business, BusinessStatus, JobRole, Occupation
from neighborly.components.character import Character, LifeStage, Pregnant, Species
from neighborly.components.location import (
    FrequentedLocations,
    Location,
    LocationPreferenceRule,
    LocationPreferences,
)
from neighborly.components.relationship import Relationship
from neighborly.components.residence import (
    Resident,
    ResidentialBuilding,
    ResidentialUnit,
    Vacant,
)
from neighborly.components.settlement import District
from neighborly.components.shared import Age
from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    BusinessSpawnTableEntry,
    CharacterSpawnTable,
    CharacterSpawnTableEntry,
    ResidenceSpawnTable,
    ResidenceSpawnTableEntry,
)
from neighborly.components.stats import Lifespan
from neighborly.components.traits import Trait, TraitType, Traits
from neighborly.config import SimulationConfig
from neighborly.datetime import MONTHS_PER_YEAR, SimDate
from neighborly.defs.definition_compiler import compile_definitions
from neighborly.ecs import Active, GameObject, System, SystemGroup, World
from neighborly.events.defaults import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeSeniorEvent,
    BecomeYoungAdultEvent,
    BirthEvent,
    HaveChildEvent,
    JoinSettlementEvent,
    NewSettlementEvent,
)
from neighborly.helpers.business import close_business, create_business
from neighborly.helpers.character import (
    create_character,
    die,
    move_into_residence,
    set_rand_age,
)
from neighborly.helpers.location import score_location
from neighborly.helpers.residence import create_residence
from neighborly.helpers.settlement import create_settlement
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import (
    add_relationship_trait,
    get_relationships_with_traits,
)
from neighborly.libraries import (
    BeliefLibrary,
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    EffectLibrary,
    JobRoleLibrary,
    LocationPreferenceLibrary,
    PreconditionLibrary,
    ResidenceLibrary,
    SettlementLibrary,
    SkillLibrary,
    SpeciesLibrary,
    TraitLibrary,
)
from neighborly.life_event import add_to_personal_history, dispatch_life_event


class InitializationSystems(SystemGroup):
    """A group of systems that run once at the beginning of the simulation.

    Any content initialization systems or initial world building systems should
    belong to this group.
    """

    def on_update(self, world: World) -> None:
        # Run all child systems first before deactivating
        super().on_update(world)
        self.set_active(False)


class EarlyUpdateSystems(SystemGroup):
    """The early phase of the update loop."""


class UpdateSystems(SystemGroup):
    """The main phase of the update loop."""


class LateUpdateSystems(SystemGroup):
    """The late phase of the update loop."""


class DataCollectionSystems(SystemGroup):
    """System group for collecting data.

    Any system that collects data during the course of the simulation should
    belong to this group.
    """


class InitializeSettlementSystem(System):
    """Creates one or more settlement instances using simulation config settings."""

    def on_update(self, world: World) -> None:
        config = world.resource_manager.get_resource(SimulationConfig)

        definition_ids = config.settlement

        rng = world.resource_manager.get_resource(random.Random)

        if isinstance(definition_ids, str):
            if definition_ids:
                settlement = create_settlement(world, definition_ids)
                event = NewSettlementEvent(settlement)
                dispatch_life_event(world, event)
                add_to_personal_history(settlement, event)

        elif len(definition_ids) > 0:
            choice = rng.choice(definition_ids)
            settlement = create_settlement(world, choice)
            event = NewSettlementEvent(settlement)
            dispatch_life_event(world, event)
            add_to_personal_history(settlement, event)


class SpawnResidentialBuildingsSystem(System):
    """Attempt to build new residential buildings in all districts."""

    @staticmethod
    def get_random_single_family_building(district: District) -> Optional[str]:
        """Attempt to randomly select a single-family building from the spawn table.

        Parameters
        ----------
        district
            The district where the residential building will be built.

        Returns
        -------
        str or None
            The definition ID of a selected residence, or None if no eligible entries.
        """
        with district.gameobject.world.session.begin() as session:
            eligible_entries = session.scalars(
                select(ResidenceSpawnTableEntry)
                .where(
                    ResidenceSpawnTableEntry.instances
                    < ResidenceSpawnTableEntry.max_instances
                )
                .where(
                    ResidenceSpawnTableEntry.required_population <= district.population
                )
                .where(ResidenceSpawnTableEntry.uid == district.gameobject.uid)
                .where(
                    ResidenceSpawnTableEntry.is_multifamily == False
                )  # pylint: disable=C0121
            ).all()

        if len(eligible_entries) == 0:
            return None

        rng = district.gameobject.world.resource_manager.get_resource(random.Random)

        population = [e.name for e in eligible_entries]
        weights = [e.spawn_frequency for e in eligible_entries]

        return rng.choices(
            population=population,
            weights=weights,
            k=1,
        )[0]

    @staticmethod
    def get_random_multifamily_building(district: District) -> Optional[str]:
        """Attempt to randomly select a multifamily building from the spawn table.

        Parameters
        ----------
        district
            The district where the residential building will be built.

        Returns
        -------
        str or None
            The definition ID of a selected residence, or None if no eligible entries.
        """
        with district.gameobject.world.session.begin() as session:
            eligible_entries = session.scalars(
                select(ResidenceSpawnTableEntry)
                .where(
                    ResidenceSpawnTableEntry.instances
                    < ResidenceSpawnTableEntry.max_instances
                )
                .where(
                    ResidenceSpawnTableEntry.required_population <= district.population
                )
                .where(ResidenceSpawnTableEntry.uid == district.gameobject.uid)
                .where(
                    ResidenceSpawnTableEntry.is_multifamily
                    == True  # pylint: disable=C0121
                )
            ).all()

        if len(eligible_entries) == 0:
            return None

        rng = district.gameobject.world.resource_manager.get_resource(random.Random)

        population = [e.name for e in eligible_entries]
        weights = [e.spawn_frequency for e in eligible_entries]

        return rng.choices(
            population=population,
            weights=weights,
            k=1,
        )[0]

    def on_update(self, world: World) -> None:
        for _, (_, district, spawn_table) in world.get_components(
            (Active, District, ResidenceSpawnTable)
        ):
            # We can't build if there is no space
            if district.residential_slots <= 0:
                continue

            # Try to build a multifamily residential building
            multifamily_building = (
                SpawnResidentialBuildingsSystem.get_random_multifamily_building(
                    district=district
                )
            )

            if multifamily_building is not None:
                residence = create_residence(
                    world,
                    multifamily_building,
                )
                residence.get_component(ResidentialBuilding).district = (
                    district.gameobject
                )
                district.add_residence(residence)
                district.gameobject.add_child(residence)
                spawn_table.increment_count(multifamily_building)
                continue

            # Try to build a single-family residential building
            single_family_building = (
                SpawnResidentialBuildingsSystem.get_random_single_family_building(
                    district=district
                )
            )

            if single_family_building is not None:
                residence = create_residence(
                    world,
                    single_family_building,
                )
                residence.get_component(ResidentialBuilding).district = (
                    district.gameobject
                )
                district.add_residence(residence)
                district.gameobject.add_child(residence)
                spawn_table.increment_count(single_family_building)


class SpawnNewResidentSystem(System):
    """Spawns new characters as residents within vacant residences."""

    CHANCE_NEW_RESIDENT: ClassVar[float] = 0.5

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        # Find vacant residences
        for _, (_, residence, _) in world.get_components(
            (Active, ResidentialUnit, Vacant)
        ):
            # Get the spawn table of district the residence belongs to
            district = residence.building.get_component(ResidentialBuilding).district

            assert district is not None

            spawn_table = district.get_component(CharacterSpawnTable)

            if len(spawn_table) == 0:
                continue

            if rng.random() > SpawnNewResidentSystem.CHANCE_NEW_RESIDENT:
                continue

            with world.session.begin() as session:
                eligible_entries = session.scalars(
                    select(CharacterSpawnTableEntry).where(
                        CharacterSpawnTableEntry.uid == district.uid
                    )
                ).all()

            # Weighted random selection on the characters in the table
            population = [e.name for e in eligible_entries]
            weights = [e.spawn_frequency for e in eligible_entries]

            character_definition_id = rng.choices(
                population=population,
                weights=weights,
                k=1,
            )[0]

            character_life_stage = rng.choices(
                population=(LifeStage.YOUNG_ADULT, LifeStage.ADULT, LifeStage.SENIOR),
                weights=(5, 2, 1),
                k=1,
            )[0]

            character = create_character(world, character_definition_id)

            set_rand_age(character, character_life_stage)

            settlement = district.get_component(District).settlement
            assert settlement is not None

            event = JoinSettlementEvent(
                character,
                settlement,
            )

            dispatch_life_event(world, event)
            add_to_personal_history(character, event)

            # Add the character as the owner of the home and a resident
            move_into_residence(character, residence.gameobject, is_owner=True)


class SpawnNewBusinessesSystem(System):
    """Spawns new businesses for characters to open."""

    @staticmethod
    def get_random_business(district: District) -> Optional[str]:
        """Attempt to randomly select a business from the spawn table.

        Parameters
        ----------
        district
            The district where the business will be built.

        Returns
        -------
        str or None
            The definition ID of a selected business, or None if no eligible entries.
        """
        with district.gameobject.world.session.begin() as session:
            eligible_entries = session.scalars(
                select(BusinessSpawnTableEntry).where(
                    BusinessSpawnTableEntry.uid == district.gameobject.uid
                )
            ).all()

        if len(eligible_entries) == 0:
            return None

        rng = district.gameobject.world.resource_manager.get_resource(random.Random)

        population = [e.name for e in eligible_entries]
        weights = [e.spawn_frequency for e in eligible_entries]

        return rng.choices(
            population=population,
            weights=weights,
            k=1,
        )[0]

    def on_update(self, world: World) -> None:
        for _, (_, district, spawn_table) in world.get_components(
            (Active, District, BusinessSpawnTable)
        ):
            # We can't build if there is no space
            if district.business_slots <= 0:
                continue

            business_id = SpawnNewBusinessesSystem.get_random_business(
                district=district
            )

            if business_id is not None:
                business = create_business(world, business_id)
                business.get_component(Business).district = district.gameobject
                district.add_business(business)
                district.gameobject.add_child(business)
                spawn_table.increment_count(business_id)


class CompileTraitDefsSystem(System):
    """Instantiates all the trait definitions within the TraitLibrary."""

    def on_update(self, world: World) -> None:
        trait_library = world.resource_manager.get_resource(TraitLibrary)
        effect_library = world.resource_manager.get_resource(EffectLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(trait_library.definitions.values())

        # Clear out the unprocessed ones
        trait_library.definitions.clear()

        # Add the new definitions and instances to the library.
        for trait_def in compiled_defs:
            if not trait_def.is_template:
                trait_library.add_definition(trait_def)

                trait_library.add_trait(
                    Trait(
                        definition_id=trait_def.definition_id,
                        name=trait_def.name,
                        trait_type=TraitType[trait_def.trait_type.upper()],
                        description=trait_def.description,
                        effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in trait_def.effects
                        ],
                        conflicting_traits=trait_def.conflicts_with,
                        target_effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in trait_def.target_effects
                        ],
                        owner_effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in trait_def.owner_effects
                        ],
                        outgoing_relationship_effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in trait_def.outgoing_relationship_effects
                        ],
                        incoming_relationship_effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in trait_def.incoming_relationship_effects
                        ],
                    )
                )


class CompileSpeciesDefsSystem(System):
    """Instantiates all the species definitions within the SpeciesLibrary."""

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(SpeciesLibrary)
        effect_library = world.resource_manager.get_resource(EffectLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)

                library.add_species(
                    Species(
                        definition_id=definition.definition_id,
                        name=definition.name,
                        description=definition.description,
                        effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in definition.effects
                        ],
                        conflicting_traits=definition.conflicts_with,
                        adolescent_age=definition.adolescent_age,
                        young_adult_age=definition.young_adult_age,
                        adult_age=definition.adult_age,
                        senior_age=definition.senior_age,
                        lifespan=definition.lifespan,
                        can_physically_age=definition.can_physically_age,
                    )
                )


class CompileSkillDefsSystem(System):
    """Instantiates all the skill definitions within the SkillLibrary."""

    def on_update(self, world: World) -> None:
        skill_library = world.resource_manager.get_resource(SkillLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(skill_library.definitions.values())

        # Clear out the unprocessed ones
        skill_library.definitions.clear()

        # Add the new definitions and instances to the library.
        for skill_def in compiled_defs:
            if not skill_def.is_template:
                skill_library.add_definition(skill_def)


class CompileJobRoleDefsSystem(System):
    """Instantiates all the job role definitions within the TraitLibrary."""

    def on_update(self, world: World) -> None:
        job_role_library = world.resource_manager.get_resource(JobRoleLibrary)
        effect_library = world.resource_manager.get_resource(EffectLibrary)
        precondition_library = world.resource_manager.get_resource(PreconditionLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(job_role_library.definitions.values())

        # Clear out the unprocessed ones
        job_role_library.definitions.clear()

        # Add the new definitions and instances to the library.
        for role_def in compiled_defs:
            if not role_def.is_template:
                job_role_library.add_definition(role_def)

                job_role_library.add_role(
                    JobRole(
                        definition_id=role_def.definition_id,
                        name=role_def.name,
                        job_level=role_def.job_level,
                        description=role_def.description,
                        requirements=[
                            precondition_library.create_from_obj(world, entry)
                            for entry in role_def.requirements
                        ],
                        effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in role_def.effects
                        ],
                        recurring_effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in role_def.recurring_effects
                        ],
                    )
                )


class CompileDistrictDefsSystem(System):
    """Compile district definitions."""

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(DistrictLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class CompileLocationPreferenceDefsSystem(System):
    """Compile location preference definitions."""

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(LocationPreferenceLibrary)
        precondition_library = world.resource_manager.get_resource(PreconditionLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)

                library.add_rule(
                    LocationPreferenceRule(
                        rule_id=definition.rule_id,
                        preconditions=[
                            precondition_library.create_from_obj(world, entry)
                            for entry in definition.preconditions
                        ],
                        probability=definition.probability,
                    )
                )


class CompileBeliefDefsSystem(System):
    """Compile belief definitions."""

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(BeliefLibrary)
        effect_library = world.resource_manager.get_resource(EffectLibrary)
        precondition_library = world.resource_manager.get_resource(PreconditionLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)

                library.add_belief(
                    Belief(
                        belief_id=definition.belief_id,
                        description=definition.description,
                        preconditions=[
                            precondition_library.create_from_obj(world, entry)
                            for entry in definition.preconditions
                        ],
                        effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in definition.effects
                        ],
                        is_global=definition.is_global,
                    )
                )


class CompileSettlementDefsSystem(System):
    """Compile settlement definitions."""

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(SettlementLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class CompileResidenceDefsSystem(System):
    """Compile residence definitions."""

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(ResidenceLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class CompileCharacterDefsSystem(System):
    """Compile character definitions."""

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(CharacterLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class CompileBusinessDefsSystem(System):
    """Compile business definitions."""

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(BusinessLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class UpdateFrequentedLocationSystem(System):
    """Characters update the locations that they frequent

    This system runs on a regular interval to allow characters to update the locations
    that they frequent to reflect their current status and the state of the settlement.
    It allows characters to choose new places to frequent that maybe didn't exist prior.
    """

    __slots__ = "ideal_location_count", "location_score_threshold"

    ideal_location_count: int
    """The ideal number of frequented locations that characters should have"""

    location_score_threshold: float
    """The probability score required for to consider frequenting a location."""

    def __init__(
        self, ideal_location_count: int = 4, location_score_threshold: float = 0.4
    ) -> None:
        super().__init__()
        self.ideal_location_count = ideal_location_count
        self.location_score_threshold = location_score_threshold

    def score_locations(
        self,
        character: GameObject,
    ) -> tuple[list[float], list[GameObject]]:
        """Score potential locations for the character to frequent.

        Parameters
        ----------
        character
            The character to score the location in reference to

        Returns
        -------
        Tuple[list[float], list[GameObject]]
            A list of tuples containing location scores and the location, sorted in
            descending order
        """

        scores: list[float] = []
        locations: list[GameObject] = []

        for _, (business, location, _) in character.world.get_components(
            (Business, Location, Active)
        ):
            if business.status != BusinessStatus.OPEN:
                continue

            if location.is_private:
                continue

            score = score_location(character, business.gameobject)
            if score >= self.location_score_threshold:
                scores.append(score)
                locations.append(business.gameobject)

        return scores, locations

    def on_update(self, world: World) -> None:
        # Frequented locations are sampled from the current settlement
        # that the character belongs to
        rng = world.resource_manager.get_resource(random.Random)

        for _, (
            frequented_locations,
            _,
            character,
            _,
        ) in world.get_components(
            (FrequentedLocations, LocationPreferences, Character, Active)
        ):
            if character.life_stage < LifeStage.YOUNG_ADULT:
                continue

            if len(frequented_locations) < self.ideal_location_count:
                # Try to find additional places to frequent
                places_to_find = max(
                    0, self.ideal_location_count - len(frequented_locations)
                )

                scores, locations = self.score_locations(character.gameobject)

                if locations:
                    chosen_locations = rng.choices(
                        population=locations, weights=scores, k=places_to_find
                    )

                    for location in chosen_locations:
                        if location not in frequented_locations:
                            frequented_locations.add_location(location)


class AgingSystem(System):
    """Increases the age of all active GameObjects with Age components."""

    def on_update(self, world: World) -> None:
        # This system runs every simulated month
        elapsed_years: float = 1.0 / MONTHS_PER_YEAR

        for _, (age, _) in world.get_components((Age, Active)):
            age.value += elapsed_years


class LifeStageSystem(System):
    """Updates the life stage of all characters to reflect their current age."""

    def on_update(self, world: World) -> None:

        for _, (character, age, _) in world.get_components((Character, Age, Active)):
            species = character.species

            if species.can_physically_age:
                if age.value >= species.senior_age:
                    if character.life_stage != LifeStage.SENIOR:
                        evt = BecomeSeniorEvent(character.gameobject)
                        character.life_stage = LifeStage.SENIOR
                        dispatch_life_event(world, evt)
                        add_to_personal_history(character.gameobject, evt)

                elif age.value >= species.adult_age:
                    if character.life_stage != LifeStage.ADULT:
                        evt = BecomeAdultEvent(character.gameobject)
                        character.life_stage = LifeStage.ADULT
                        dispatch_life_event(world, evt)
                        add_to_personal_history(character.gameobject, evt)

                elif age.value >= species.young_adult_age:
                    if character.life_stage != LifeStage.YOUNG_ADULT:
                        evt = BecomeYoungAdultEvent(character.gameobject)
                        character.life_stage = LifeStage.YOUNG_ADULT
                        dispatch_life_event(world, evt)
                        add_to_personal_history(character.gameobject, evt)

                elif age.value >= species.adolescent_age:
                    if character.life_stage != LifeStage.ADOLESCENT:
                        evt = BecomeAdolescentEvent(character.gameobject)
                        character.life_stage = LifeStage.ADOLESCENT
                        dispatch_life_event(world, evt)
                        add_to_personal_history(character.gameobject, evt)

                else:
                    if character.life_stage != LifeStage.CHILD:
                        character.life_stage = LifeStage.CHILD


class PassiveReputationChange(System):
    """Reputation stats have a probability of changing each time step."""

    CHANCE_OF_CHANGE: ClassVar[float] = 0.05

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (
            relationship,
            _,
        ) in world.get_components((Relationship, Active)):
            interaction_boost = max(
                1.0, get_stat(relationship.gameobject, "interaction_score").value / 10.0
            )

            final_chance = PassiveReputationChange.CHANCE_OF_CHANGE * (
                1.0 + interaction_boost
            )

            if rng.random() < final_chance:
                get_stat(relationship.gameobject, "reputation").base_value = (
                    get_stat(relationship.gameobject, "reputation").base_value
                    + get_stat(relationship.gameobject, "compatibility").value
                )


class PassiveRomanceChange(System):
    """Romance stats have a probability of changing each time step."""

    CHANCE_OF_CHANGE: ClassVar[float] = 0.05

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (
            relationship,
            _,
        ) in world.get_components((Relationship, Active)):
            interaction_boost = max(
                1.0, get_stat(relationship.gameobject, "interaction_score").value / 10.0
            )

            final_chance = PassiveRomanceChange.CHANCE_OF_CHANGE * (
                1.0 + interaction_boost
            )

            if rng.random() < final_chance:
                get_stat(relationship.gameobject, "romance").base_value = (
                    get_stat(relationship.gameobject, "romance").base_value
                    + get_stat(relationship.gameobject, "romantic_compatibility").value
                )


class CharacterLifespanSystem(System):
    """Kills of characters who have reached their lifespan."""

    def on_update(self, world: World) -> None:
        for _, (character, age, life_span, _) in world.get_components(
            (Character, Age, Lifespan, Active)
        ):

            if age.value >= life_span.stat.value:
                die(character.gameobject)


class BusinessLifespanSystem(System):
    """Kills of business that have reached their lifespan."""

    def on_update(self, world: World) -> None:
        for _, (business, age, lifespan, _) in world.get_components(
            (Business, Age, Lifespan, Active)
        ):
            if age.value >= lifespan.stat.value and business.owner:
                close_business(business.gameobject)


class ChildBirthSystem(System):
    """Spawns new children when pregnant characters reach their due dates."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDate)

        for _, (character, pregnancy, _) in world.get_components(
            (Character, Pregnant, Active)
        ):
            if pregnancy.due_date > current_date:
                continue

            other_parent = pregnancy.partner

            baby = create_character(
                character.gameobject.world,
                character.gameobject.metadata["definition_id"],
            )

            baby.get_component(Character).last_name = character.last_name

            move_into_residence(
                baby,
                character.gameobject.get_component(Resident).residence,
                is_owner=False,
            )

            # Birthing parent to child
            add_relationship_trait(character.gameobject, baby, "child")
            add_relationship_trait(baby, character.gameobject, "parent")
            add_relationship_trait(baby, character.gameobject, "biological_parent")

            # Other parent to child
            add_relationship_trait(other_parent, baby, "child")
            add_relationship_trait(baby, other_parent, "parent")
            add_relationship_trait(baby, other_parent, "biological_parent")

            # Create relationships with children of birthing parent
            for relationship in get_relationships_with_traits(
                character.gameobject, "child"
            ):
                rel = relationship.get_component(Relationship)

                if rel.target == baby:
                    continue

                sibling = rel.target

                # Baby to sibling
                add_relationship_trait(baby, sibling, "sibling")
                add_relationship_trait(sibling, baby, "sibling")

            # Create relationships with children of the birthing parent's spouses
            for spousal_rel in get_relationships_with_traits(
                character.gameobject, "spouse"
            ):
                spouse = spousal_rel.get_component(Relationship).target

                if spousal_rel.is_active:
                    add_relationship_trait(spouse, baby, "child")
                    add_relationship_trait(baby, spouse, "parent")

                for child_rel in get_relationships_with_traits(spouse, "child"):
                    rel = child_rel.get_component(Relationship)
                    if rel.target == baby:
                        continue

                    sibling = rel.target

                    # Baby to sibling
                    add_relationship_trait(baby, sibling, "sibling")
                    add_relationship_trait(sibling, baby, "sibling")

            # Create relationships with children of other parent
            for relationship in get_relationships_with_traits(other_parent, "child"):
                rel = relationship.get_component(Relationship)
                if rel.target == baby:
                    continue

                sibling = rel.target

                # Baby to sibling
                add_relationship_trait(baby, sibling, "sibling")
                add_relationship_trait(sibling, baby, "sibling")

            character.gameobject.remove_component(Pregnant)
            get_stat(character.gameobject, "fertility").base_value -= 0.2

            have_child_evt = HaveChildEvent(
                character.gameobject,
                other_parent,
                baby,
            )
            dispatch_life_event(world, have_child_evt)
            add_to_personal_history(character.gameobject, have_child_evt)
            add_to_personal_history(other_parent, have_child_evt)

            birth_evt = BirthEvent(baby)
            dispatch_life_event(world, birth_evt)
            add_to_personal_history(baby, birth_evt)


class JobRoleMonthlyEffectsSystem(System):
    """This system applies monthly effects associated with character's job roles.

    Unlike the normal effects, monthly effects are not reversed when the character
    leaves the role. The changes are permanent. This system is meant to give characters
    a way of increasing specific skill points the longer they work at a job. This way
    higher level jobs can require characters to meet skill thresholds.
    """

    def on_update(self, world: World) -> None:
        for _, (occupation, _) in world.get_components((Occupation, Active)):
            for effect in occupation.job_role.recurring_effects:
                effect.apply(occupation.gameobject)


class TickTraitsSystem(System):
    """Update trait durations."""

    def on_update(self, world: World) -> None:
        for _, (traits,) in world.get_components((Traits,)):
            traits_to_remove: list[Trait] = []

            with world.session.begin() as session:

                for trait_instance in traits.traits.values():
                    if not trait_instance.has_duration:
                        continue

                    trait_instance.duration -= 1

                    if trait_instance.duration <= 0:
                        session.delete(trait_instance)
                        traits_to_remove.append(trait_instance.trait)
                    else:
                        session.add(trait_instance)

            for trait_id in traits_to_remove:
                traits.remove_trait(trait_id)
