"""Built-in Systems.

This module contains built-in systems that help simulations function.

"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import ClassVar, Optional

import polars as pl

from neighborly.components.business import JobRole, Occupation
from neighborly.components.character import Character, LifeStage, Species
from neighborly.components.location import FrequentedLocations, Location
from neighborly.components.relationship import Relationship
from neighborly.components.residence import Resident, ResidentialUnit, Vacant
from neighborly.components.settlement import District
from neighborly.components.skills import Skill, Skills
from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    CharacterSpawnTable,
    ResidenceSpawnTable,
)
from neighborly.components.stats import Stats
from neighborly.components.traits import Trait, Traits
from neighborly.config import SimulationConfig
from neighborly.datetime import MONTHS_PER_YEAR, SimDate
from neighborly.definition_compiler import compile_definitions
from neighborly.defs.base_types import (
    BusinessGenOptions,
    CharacterGenOptions,
    JobRoleDef,
    ResidenceGenOptions,
    SettlementGenOptions,
    SkillDef,
    TraitDef,
)
from neighborly.ecs import Active, GameObject, System, SystemGroup, World
from neighborly.events.defaults import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeSeniorEvent,
    BecomeYoungAdultEvent,
    BirthEvent,
    ChangeResidenceEvent,
    Death,
    HaveChildEvent,
    JoinSettlementEvent,
)
from neighborly.helpers.business import create_business
from neighborly.helpers.character import create_character
from neighborly.helpers.location import score_location
from neighborly.helpers.relationship import (
    add_relationship,
    get_relationship,
    get_relationships_with_traits,
    has_relationship,
)
from neighborly.helpers.residence import create_residence
from neighborly.helpers.settlement import create_settlement
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, remove_trait
from neighborly.libraries import (
    JobRoleLibrary,
    LifeEventLibrary,
    SettlementLibrary,
    SkillLibrary,
    TraitLibrary,
)
from neighborly.life_event import LifeEvent


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


class InitializeSettlementSystem(System):
    """Creates a settlement instance using simulation config settings."""

    def on_update(self, world: World) -> None:
        config = world.resources.get_resource(SimulationConfig)
        settlement_library = world.resources.get_resource(SettlementLibrary)

        if not settlement_library.definitions:
            raise RuntimeError(
                "No settlement definitions have been loaded into the library."
            )

        if config.settlement_with_id:
            create_settlement(
                world, SettlementGenOptions(definition_id=config.settlement_with_id)
            )
            return

        elif config.settlement_with_tags:
            potential_defs = settlement_library.get_definition_with_tags(
                config.settlement_with_tags
            )

            if potential_defs:
                settlement_def = world.rng.choice(potential_defs)

                create_settlement(
                    world,
                    SettlementGenOptions(definition_id=settlement_def.definition_id),
                )

                return

        # Just choose one at random

        potential_defs = list(settlement_library.definitions.values())

        settlement_def = world.rng.choice(potential_defs)

        create_settlement(
            world, SettlementGenOptions(definition_id=settlement_def.definition_id)
        )


class SpawnResidentialBuildingsSystem(System):
    """Attempt to build new residential buildings in all districts."""

    @staticmethod
    def get_random_single_family_building(
        district: District, spawn_table: ResidenceSpawnTable
    ) -> Optional[str]:
        """Attempt to randomly select a single-family building from the spawn table.

        Parameters
        ----------
        district
            The district where the residential building will be built.
        spawn_table
            The spawn table where buildings are sampled from.

        Returns
        -------
        str or None
            The definition ID of a selected residence, or None if no eligible entries.
        """
        eligible_entries: pl.DataFrame = spawn_table.table.filter(  # type: ignore
            (pl.col("instances") < pl.col("max_instances"))
            & (pl.col("required_population") <= district.population)
            & (pl.col("is_multifamily") == False)  # pylint: disable=C0121
        )

        if len(eligible_entries) == 0:
            return None

        rng = district.gameobject.world.resources.get_resource(random.Random)

        return rng.choices(
            population=eligible_entries["name"].to_list(),
            weights=eligible_entries["spawn_frequency"].to_list(),
            k=1,
        )[0]

    @staticmethod
    def get_random_multifamily_building(
        district: District, spawn_table: ResidenceSpawnTable
    ) -> Optional[str]:
        """Attempt to randomly select a multifamily building from the spawn table.

        Parameters
        ----------
        district
            The district where the residential building will be built.
        spawn_table
            The spawn table where buildings are sampled from.

        Returns
        -------
        str or None
            The definition ID of a selected residence, or None if no eligible entries.
        """
        eligible_entries: pl.DataFrame = spawn_table.table.filter(  # type: ignore
            (pl.col("instances") < pl.col("max_instances"))
            & (pl.col("required_population") <= district.population)
            & (pl.col("is_multifamily") == True)  # pylint: disable=C0121
        )

        if len(eligible_entries) == 0:
            return None

        rng = district.gameobject.world.resources.get_resource(random.Random)

        return rng.choices(
            population=eligible_entries["name"].to_list(),
            weights=eligible_entries["spawn_frequency"].to_list(),
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
                    district=district, spawn_table=spawn_table
                )
            )

            if multifamily_building is not None:
                residence = create_residence(
                    world,
                    district.gameobject,
                    ResidenceGenOptions(definition_id=multifamily_building),
                )
                district.add_residence(residence)
                district.gameobject.add_child(residence)
                spawn_table.increment_count(multifamily_building)
                continue

            # Try to build a single-family residential building
            single_family_building = (
                SpawnResidentialBuildingsSystem.get_random_single_family_building(
                    district=district, spawn_table=spawn_table
                )
            )

            if single_family_building is not None:
                residence = create_residence(
                    world,
                    district.gameobject,
                    ResidenceGenOptions(definition_id=single_family_building),
                )
                district.add_residence(residence)
                district.gameobject.add_child(residence)
                spawn_table.increment_count(single_family_building)


class SpawnNewResidentSystem(System):
    """Spawns new characters as residents within vacant residences."""

    CHANCE_NEW_RESIDENT: ClassVar[float] = 0.5

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)

        # Find vacant residences
        for _, (_, residence, _) in world.get_components(
            (Active, ResidentialUnit, Vacant)
        ):
            # Get the spawn table of district the residence belongs to
            spawn_table = residence.district.get_component(CharacterSpawnTable)

            if len(spawn_table.table) == 0:
                continue

            if rng.random() > SpawnNewResidentSystem.CHANCE_NEW_RESIDENT:
                continue

            # Weighted random selection on the characters in the table
            characters = spawn_table.table["name"].to_list()
            weights = spawn_table.table["spawn_frequency"].to_list()

            character_definition_id: str = rng.choices(
                population=characters, weights=weights, k=1
            )[0]

            character_life_stage = rng.choices(
                population=(LifeStage.YOUNG_ADULT, LifeStage.ADULT, LifeStage.SENIOR),
                weights=(5, 2, 1),
                k=1,
            )[0]

            character = create_character(
                world,
                CharacterGenOptions(
                    definition_id=character_definition_id,
                    life_stage=character_life_stage.name,
                ),
            )

            JoinSettlementEvent(
                subject=character,
                settlement=residence.district.get_component(District).settlement,
            ).dispatch()

            # Add the character as the owner of the home and a resident
            ChangeResidenceEvent(
                subject=character, new_residence=residence.gameobject, is_owner=True
            ).dispatch()


class SpawnNewBusinessesSystem(System):
    """Spawns new businesses for characters to open."""

    @staticmethod
    def get_random_business(
        district: District, spawn_table: BusinessSpawnTable
    ) -> Optional[str]:
        """Attempt to randomly select a business from the spawn table.

        Parameters
        ----------
        district
            The district where the business will be built.
        spawn_table
            The spawn table where businesses are sampled from.

        Returns
        -------
        str or None
            The definition ID of a selected business, or None if no eligible entries.
        """
        eligible_entries: pl.DataFrame = spawn_table.table.filter(  # type: ignore
            (pl.col("instances") < pl.col("max_instances"))
            & (pl.col("min_population") <= district.population)
        )

        if len(eligible_entries) == 0:
            return None

        rng = district.gameobject.world.resources.get_resource(random.Random)

        return rng.choices(
            population=eligible_entries["name"].to_list(),
            weights=eligible_entries["spawn_frequency"].to_list(),
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
                district=district, spawn_table=spawn_table
            )

            if business_id is not None:
                business = create_business(
                    world,
                    district.gameobject,
                    BusinessGenOptions(definition_id=business_id),
                )
                district.add_business(business)
                district.gameobject.add_child(business)
                spawn_table.increment_count(business_id)


class InstantiateTraitsSystem(System):
    """Instantiates all the trait definitions within the TraitLibrary."""

    def on_update(self, world: World) -> None:
        trait_library = world.resources.get_resource(TraitLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(
            TraitDef, trait_library.definitions.values()
        )

        # Clear out the unprocessed ones
        trait_library.definitions.clear()

        for trait_def in compiled_defs:
            trait_library.add_definition(trait_def)
            trait = world.gameobjects.spawn_gameobject(name=trait_def.display_name)
            trait.add_component(
                Trait(
                    definition_id=trait_def.definition_id,
                    display_name=trait_def.display_name,
                    description=trait_def.description,
                    stat_modifiers=trait_def.stat_modifiers,
                    skill_modifiers=trait_def.skill_modifiers,
                    conflicting_traits=trait_def.conflicts_with,
                )
            )
            trait_library.add_trait(trait)


class InstantiateSkillsSystem(System):
    """Instantiates all the skill definitions within the SkillLibrary."""

    def on_update(self, world: World) -> None:
        skill_library = world.resources.get_resource(SkillLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(
            SkillDef, skill_library.definitions.values()
        )

        # Clear out the unprocessed ones
        skill_library.definitions.clear()

        for skill_def in compiled_defs:
            skill_library.add_definition(skill_def)
            skill = world.gameobjects.spawn_gameobject(name=skill_def.display_name)
            skill.add_component(
                Skill(
                    definition_id=skill_def.definition_id,
                    display_name=skill_def.display_name,
                    description=skill_def.description,
                )
            )
            skill_library.add_skill(skill)


class InstantiateJobRolesSystem(System):
    """Instantiates all the job role definitions within the TraitLibrary."""

    def on_update(self, world: World) -> None:
        job_role_library = world.resources.get_resource(JobRoleLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(
            JobRoleDef, job_role_library.definitions.values()
        )

        # Clear out the unprocessed ones
        job_role_library.definitions.clear()

        for role_def in compiled_defs:
            job_role = world.gameobjects.spawn_gameobject(name=role_def.display_name)
            job_role.add_component(
                JobRole(
                    definition_id=role_def.definition_id,
                    display_name=role_def.display_name,
                    description=role_def.description,
                    job_level=role_def.job_level,
                    requirements=role_def.requirements,
                    stat_modifiers=role_def.stat_modifiers,
                    periodic_stat_boosts=role_def.periodic_stat_boosts,
                    periodic_skill_boosts=role_def.periodic_skill_boosts,
                )
            )
            job_role_library.add_role(job_role)


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

        for _, (location, _) in character.world.get_components((Location, Active)):

            if location.is_private:
                continue

            score = score_location(character, location.gameobject)

            if score >= self.location_score_threshold:
                scores.append(score)
                locations.append(location.gameobject)

        return scores, locations

    def on_update(self, world: World) -> None:
        # Frequented locations are sampled from the current settlement
        # that the character belongs to
        rng = world.resources.get_resource(random.Random)

        for _, (
            frequented_locations,
            character,
            _,
        ) in world.get_components((FrequentedLocations, Character, Active)):
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

        for _, (character, _) in world.get_components((Character, Active)):
            character.age = character.age + elapsed_years
            species = character.species.get_component(Species)

            if species.can_physically_age:
                if character.age >= species.senior_age:
                    if character.life_stage != LifeStage.SENIOR:
                        BecomeSeniorEvent(character.gameobject).dispatch()

                elif character.age >= species.adult_age:
                    if character.life_stage != LifeStage.ADULT:
                        BecomeAdultEvent(character.gameobject).dispatch()

                elif character.age >= species.young_adult_age:
                    if character.life_stage != LifeStage.YOUNG_ADULT:
                        BecomeYoungAdultEvent(character.gameobject).dispatch()

                elif character.age >= species.adolescent_age:
                    if character.life_stage != LifeStage.ADOLESCENT:
                        BecomeAdolescentEvent(character.gameobject).dispatch()

                else:
                    if character.life_stage != LifeStage.CHILD:
                        character.life_stage = LifeStage.CHILD


class HealthDecaySystem(System):
    """Decay the health points of characters as they get older."""

    def on_update(self, world: World) -> None:
        # This system runs every simulated month
        elapsed_time: float = 1.0 / MONTHS_PER_YEAR

        for _, (
            _,
            character,
        ) in world.get_components((Active, Character)):
            get_stat(character.gameobject, "health").base_value -= (
                get_stat(character.gameobject, "health_decay").value * elapsed_time
            )


class PassiveReputationChange(System):
    """Reputation stats have a probability of changing each time step."""

    CHANCE_OF_CHANGE: ClassVar[float] = 0.05

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)

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
        rng = world.resources.get_resource(random.Random)

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


class DeathSystem(System):
    """Characters die when their health hits zero."""

    def on_update(self, world: World) -> None:
        for _, (_, character) in world.get_components((Active, Character)):
            if get_stat(character.gameobject, "health").value <= 0:
                Death(character.gameobject).dispatch()


class ChildBirthSystem(System):
    """Spawns new children when pregnant characters reach their due dates."""

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        for _, (character, traits, _) in world.get_components(
            (Character, Traits, Active)
        ):
            if not traits.has_trait("pregnant"):
                continue

            pregnancy = traits.get_trait("pregnant")

            if pregnancy.data["due_date"] > current_date:
                continue

            other_parent: GameObject = pregnancy.data["partner"]

            baby = create_character(
                character.gameobject.world,
                CharacterGenOptions(
                    definition_id=character.gameobject.metadata["definition_id"],
                    last_name=character.last_name,
                ),
            )

            ChangeResidenceEvent(
                baby,
                new_residence=character.gameobject.get_component(Resident).residence,
                is_owner=False,
            ).dispatch()

            # Birthing parent to child
            add_trait(get_relationship(character.gameobject, baby), "child")
            add_trait(get_relationship(baby, character.gameobject), "parent")
            add_trait(get_relationship(baby, character.gameobject), "biological_parent")

            # Other parent to child
            add_trait(get_relationship(other_parent, baby), "child")
            add_trait(get_relationship(baby, other_parent), "parent")
            add_trait(get_relationship(baby, other_parent), "biological_parent")

            # Create relationships with children of birthing parent
            for relationship in get_relationships_with_traits(
                character.gameobject, "child"
            ):
                rel = relationship.get_component(Relationship)

                if rel.target == baby:
                    continue

                sibling = rel.target

                # Baby to sibling
                add_trait(get_relationship(baby, sibling), "sibling")
                add_trait(get_relationship(sibling, baby), "sibling")

            # Create relationships with children of the birthing parent's spouses
            for spousal_rel in get_relationships_with_traits(
                character.gameobject, "spouse"
            ):
                spouse = spousal_rel.get_component(Relationship).target

                if spousal_rel.is_active:
                    add_trait(get_relationship(spouse, baby), "child")
                    add_trait(get_relationship(baby, spouse), "parent")

                for child_rel in get_relationships_with_traits(spouse, "child"):
                    rel = child_rel.get_component(Relationship)
                    if rel.target == baby:
                        continue

                    sibling = rel.target

                    # Baby to sibling
                    add_trait(get_relationship(baby, sibling), "sibling")
                    add_trait(get_relationship(sibling, baby), "sibling")

            # Create relationships with children of other parent
            for relationship in get_relationships_with_traits(other_parent, "child"):
                rel = relationship.get_component(Relationship)
                if rel.target == baby:
                    continue

                sibling = rel.target

                # Baby to sibling
                add_trait(get_relationship(baby, sibling), "sibling")
                add_trait(get_relationship(sibling, baby), "sibling")

            remove_trait(character.gameobject, "pregnant")
            get_stat(character.gameobject, "fertility").base_value -= 0.2

            HaveChildEvent(
                parent_0=character.gameobject,
                parent_1=other_parent,
                child=baby,
            ).dispatch()

            BirthEvent(baby).dispatch()


class LifeEventSystem(System):
    """Simulate life events/character behavior.

    This system is the core of character behavior for the Simulation. Each time step,
    characters probabilistically select a life event to execute from a shared collection
    of LifeEvent types. Life events are how we represent character behaviors and track
    the various narrative-relevant events that happen in the simulation. Every life
    event has a 'subject' (the character who the event happens to).

    To add a new life event to this system, create a new LifeEvent subclass and add it
    to the LifeEventLibrary instance within the simulation world's resource manager.
    """

    EVENT_PROBABILITY_THRESHOLD: ClassVar[float] = 0.5
    """The minimum required probability for an event to be considered for execution."""

    def on_update(self, world: World) -> None:
        life_event_library = world.resources.get_resource(LifeEventLibrary)
        rng = world.resources.get_resource(random.Random)

        for _, (character, _) in world.get_components((Character, Active)):
            life_event_choices: list[LifeEvent] = []
            life_event_probabilities: list[float] = []

            for event_type in life_event_library:
                # Skip event types that with base probability zero
                # these are most likely events that require more than one
                # role and are triggered by other events/systems.
                # if event_type.base_probability == 0.0:
                #     continue

                event_instance = event_type.instantiate(character.gameobject)
                if event_instance is not None:
                    event_probability = event_instance.get_probability()
                    if event_probability >= self.EVENT_PROBABILITY_THRESHOLD:
                        life_event_choices.append(event_instance)
                        life_event_probabilities.append(event_probability)

            # _logger.debug(
            #     list(
            #         zip(
            #             [f.__class__.__name__ for f in life_event_choices],
            #             life_event_probabilities,
            #         )
            #     )
            # )

            if life_event_choices:
                chosen_event = rng.choices(
                    population=life_event_choices, weights=life_event_probabilities, k=1
                )[0]

                # if rng.random() < chosen_event.get_probability():
                chosen_event.dispatch()


class MeetNewPeopleSystem(System):
    """Characters introduce themselves to new people that frequent the same places.

    Notes
    -----
    This system uses a character's sociability stat score to determine the probability
    of them introducing themselves to someone else. The goal is for characters with
    higher sociability scores to form more relationships over the course of their lives.
    """

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)

        for _, (character, _, frequented_locs) in world.get_components(
            (Character, Active, FrequentedLocations)
        ):
            probability_meet_someone = get_stat(
                character.gameobject, "sociability"
            ).normalized

            if rng.random() < probability_meet_someone:
                candidate_scores: defaultdict[GameObject, int] = defaultdict(int)

                for loc in frequented_locs:
                    for other in loc.get_component(Location):
                        if other != character.gameobject and not has_relationship(
                            character.gameobject, other
                        ):
                            candidate_scores[other] += 1

                if candidate_scores:
                    rng = world.resources.get_resource(random.Random)

                    acquaintance = rng.choices(
                        list(candidate_scores.keys()),
                        weights=list(candidate_scores.values()),
                        k=1,
                    )[0]

                    add_relationship(character.gameobject, acquaintance)
                    add_relationship(acquaintance, character.gameobject)

                    # Calculate interaction scores
                    get_stat(
                        get_relationship(character.gameobject, acquaintance),
                        "interaction_score",
                    ).base_value += candidate_scores[acquaintance]

                    get_stat(
                        get_relationship(acquaintance, character.gameobject),
                        "interaction_score",
                    ).base_value += candidate_scores[acquaintance]


class JobRoleMonthlyEffectsSystem(System):
    """This system applies monthly effects associated with character's job roles.

    Unlike the normal effects, monthly effects are not reversed when the character
    leaves the role. The changes are permanent. This system is meant to give characters
    a way of increasing specific skill points the longer they work at a job. This way
    higher level jobs can require characters to meet skill thresholds.
    """

    def on_update(self, world: World) -> None:
        for _, (skills, stats, occupation, _) in world.get_components(
            (Skills, Stats, Occupation, Active)
        ):

            for skill_boost in occupation.job_role.periodic_skill_boosts:
                skills.get_skill(skill_boost.name).stat.base_value += skill_boost.value

            for stat_boost in occupation.job_role.periodic_stat_boosts:
                stats.get_stat(stat_boost.name).base_value += stat_boost.value


class TickTraitsSystem(System):
    """Update trait durations."""

    def on_update(self, world: World) -> None:
        for _, (traits,) in world.get_components((Traits,)):
            trait_instances = list(traits.traits)

            for instance in trait_instances:
                if instance.has_duration:
                    instance.duration -= 1

                    if instance.duration <= 0:
                        remove_trait(traits.gameobject, instance.trait.definition_id)
