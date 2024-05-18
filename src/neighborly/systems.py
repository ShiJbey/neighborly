"""Built-in Systems.

This module contains built-in systems that help simulations function.

"""

from __future__ import annotations

import logging
import random
from collections import defaultdict
from typing import ClassVar

from neighborly.components.beliefs import Belief
from neighborly.components.business import Business, BusinessStatus, JobRole, Occupation
from neighborly.components.character import (
    Character,
    Household,
    LifeStage,
    MemberOfHousehold,
    Pregnant,
    ResidentOf,
    Sex,
    Species,
    SpeciesType,
)
from neighborly.components.location import (
    CurrentSettlement,
    FrequentedLocations,
    Location,
    LocationPreferenceRule,
    LocationPreferences,
)
from neighborly.components.relationship import Relationship
from neighborly.components.settlement import District, Settlement
from neighborly.components.shared import Age
from neighborly.components.skills import Skill
from neighborly.components.spawn_table import CharacterSpawnTable, DistrictSpawnTable
from neighborly.components.stats import Fertility, Lifespan
from neighborly.components.traits import Trait, Traits, TraitType
from neighborly.config import SimulationConfig
from neighborly.datetime import MONTHS_PER_YEAR, SimDate
from neighborly.defs.base_types import DistrictDef
from neighborly.defs.definition_compiler import compile_definitions
from neighborly.ecs import Active, Event, GameObject, System, SystemGroup, World
from neighborly.events.defaults import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeSeniorEvent,
    BecomeYoungAdultEvent,
    BirthEvent,
    HaveChildEvent,
    JoinSettlementEvent,
    SettlementAddedEvent,
)
from neighborly.helpers.character import (
    add_character_to_household,
    create_character,
    create_child,
    create_household,
    set_household_head,
)
from neighborly.helpers.content_selection import get_with_tags
from neighborly.helpers.location import score_location
from neighborly.helpers.settlement import (
    add_district_to_settlement,
    create_district,
    create_settlement,
)
from neighborly.helpers.traits import (
    add_relationship_trait,
    get_relationships_with_traits,
    remove_relationship_trait,
    remove_trait,
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
    SettlementLibrary,
    SkillLibrary,
    SpeciesLibrary,
    TraitLibrary,
)
from neighborly.life_event import dispatch_life_event
from neighborly.plugins.actions import CloseBusiness, Die

_logger = logging.getLogger(__name__)


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
    """Creates one or more settlement instances using simulation config settings."""

    def on_update(self, world: World) -> None:
        config = world.resource_manager.get_resource(SimulationConfig)

        rng = world.resource_manager.get_resource(random.Random)

        settlement_library = world.resources.get_resource(SettlementLibrary)
        district_library = world.resources.get_resource(DistrictLibrary)

        # Select a settlement from the library using the theme tags
        selection_tags = [f"~{tag}" for tag in config.theme_tags]

        settlement_options = settlement_library.get_definition_with_tags(selection_tags)

        if not settlement_options:
            return

        chosen_settlement_definition = rng.choice(settlement_options)

        settlement = create_settlement(
            world, chosen_settlement_definition.definition_id
        ).get_component(Settlement)

        world.events.dispatch_event(
            Event("settlement-added", world=world, settlement=settlement.gameobject)
        )

        # Now generate districts for the settlement using the spawn table. The table
        # has a subset of all the districts in the district library. We need to perform
        # tag-based selection on all the entries
        spawn_table = settlement.gameobject.get_component(DistrictSpawnTable)

        districts_and_tags: list[tuple[DistrictDef, list[str]]] = []

        for entry in spawn_table.table.values():
            definition = district_library.get_definition(entry.definition_id)
            districts_and_tags.append((definition, [*definition.tags]))

        district_options = get_with_tags(districts_and_tags, selection_tags)

        n_districts_remaining = config.num_districts

        district_instance_counts: defaultdict[str, int] = defaultdict(lambda: 0)

        while n_districts_remaining > 0:

            if not district_options:
                raise RuntimeError(
                    "Ran out of eligible districts when constructing settlement. "
                    "Please adjust settings or add more content."
                )

            district_def = rng.choice(district_options)

            # If there are too many instances of this district remove it from the list
            # and try again
            if (
                district_instance_counts[district_def.definition_id]
                > district_def.max_instances
            ):
                district_options.remove(district_def)
                continue

            # Create an instance of the district and add it to the settlement
            district = create_district(world, district_def.definition_id).get_component(
                District
            )

            add_district_to_settlement(settlement, district)

            world.events.dispatch_event(
                Event("district-added", world=world, district=district)
            )

            n_districts_remaining -= 1

        event = SettlementAddedEvent(settlement.gameobject)
        dispatch_life_event(event, [settlement.gameobject])


class SpawnNewResidentSystem(System):
    """Spawns new characters as residents within vacant residences."""

    CHANCE_NEW_RESIDENT: ClassVar[float] = 0.5

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        # Find vacant residences
        for _, (_, current_settlement, spawn_table, _) in world.get_components(
            (District, CurrentSettlement, CharacterSpawnTable, Active)
        ):
            if len(spawn_table.table) == 0:
                continue

            if rng.random() > SpawnNewResidentSystem.CHANCE_NEW_RESIDENT:
                continue

            # Weighted random selection on the characters in the table
            eligible_entries: list[str] = []
            weights: list[float] = []

            for entry in spawn_table.table.values():
                eligible_entries.append(entry.definition_id)
                weights.append(entry.spawn_frequency)

            if not eligible_entries:
                continue

            character_definition_id = rng.choices(
                population=eligible_entries,
                weights=weights,
                k=1,
            )[0]

            character = create_character(world, character_definition_id)

            household = create_household(world).get_component(Household)

            set_household_head(household, character.get_component(Character))
            add_character_to_household(household, character.get_component(Character))

            character.add_component(
                ResidentOf(settlement=current_settlement.settlement)
            )

            current_settlement.settlement.get_component(Settlement).population += 1

            world.events.dispatch_event(
                Event("character-added", world=world, character=character)
            )

            event = JoinSettlementEvent(
                character,
                current_settlement.settlement,
            )

            dispatch_life_event(event, [character])


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
                        inheritance_chance_both=trait_def.inheritance_chance_both,
                        inheritance_chance_single=trait_def.inheritance_chance_single,
                        is_inheritable=(
                            trait_def.inheritance_chance_single > 0
                            or trait_def.inheritance_chance_both > 0
                        ),
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

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)

                min_lifespan, max_lifespan = tuple(
                    int(x.strip()) for x in definition.lifespan.split("-")
                )

                library.add_species(
                    SpeciesType(
                        definition_id=definition.definition_id,
                        name=definition.name,
                        description=definition.description,
                        adolescent_age=definition.adolescent_age,
                        young_adult_age=definition.young_adult_age,
                        adult_age=definition.adult_age,
                        senior_age=definition.senior_age,
                        lifespan=(min_lifespan, max_lifespan),
                        can_physically_age=definition.can_physically_age,
                        traits=[*definition.traits],
                        adolescent_female_fertility=definition.adolescent_female_fertility,
                        young_adult_female_fertility=definition.young_adult_female_fertility,
                        adult_female_fertility=definition.adult_female_fertility,
                        senior_female_fertility=definition.senior_female_fertility,
                        adolescent_male_fertility=definition.adolescent_male_fertility,
                        young_adult_male_fertility=definition.young_adult_male_fertility,
                        adult_male_fertility=definition.adult_male_fertility,
                        senior_male_fertility=definition.senior_male_fertility,
                        fertility_cost_per_child=definition.fertility_cost_per_child,
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

                skill_library.add_skill(
                    Skill(
                        definition_id=skill_def.definition_id,
                        name=skill_def.name,
                        description=skill_def.description,
                        tags=set(*skill_def.tags),
                    )
                )


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
                        rule_id=definition.definition_id,
                        description=definition.description,
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
                        belief_id=definition.definition_id,
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

        for _, (character, species, age, fertility, _) in world.get_components(
            (Character, Species, Age, Fertility, Active)
        ):

            if species.species.can_physically_age:
                if age.value >= species.species.senior_age:
                    if character.life_stage != LifeStage.SENIOR:
                        fertility_max = (
                            species.species.senior_male_fertility
                            if character.sex == Sex.MALE
                            else species.species.senior_female_fertility
                        )

                        fertility.stat.base_value = min(
                            fertility.stat.base_value, fertility_max
                        )

                        evt = BecomeSeniorEvent(character.gameobject)
                        character.life_stage = LifeStage.SENIOR
                        dispatch_life_event(evt, [character.gameobject])

                elif age.value >= species.species.adult_age:
                    if character.life_stage != LifeStage.ADULT:

                        fertility_max = (
                            species.species.adult_male_fertility
                            if character.sex == Sex.MALE
                            else species.species.adult_female_fertility
                        )
                        fertility.stat.base_value = min(
                            fertility.stat.base_value, fertility_max
                        )

                        evt = BecomeAdultEvent(character.gameobject)
                        character.life_stage = LifeStage.ADULT
                        dispatch_life_event(evt, [character.gameobject])

                elif age.value >= species.species.young_adult_age:
                    if character.life_stage != LifeStage.YOUNG_ADULT:

                        fertility_max = (
                            species.species.young_adult_male_fertility
                            if character.sex == Sex.MALE
                            else species.species.young_adult_female_fertility
                        )

                        fertility.stat.base_value = min(
                            fertility.stat.base_value, fertility_max
                        )

                        evt = BecomeYoungAdultEvent(character.gameobject)
                        character.life_stage = LifeStage.YOUNG_ADULT
                        dispatch_life_event(evt, [character.gameobject])

                elif age.value >= species.species.adolescent_age:
                    if character.life_stage != LifeStage.ADOLESCENT:

                        fertility_max = (
                            species.species.adolescent_male_fertility
                            if character.sex == Sex.MALE
                            else species.species.adolescent_female_fertility
                        )

                        fertility.stat.base_value = min(
                            fertility.stat.base_value, fertility_max
                        )

                        evt = BecomeAdolescentEvent(character.gameobject)
                        character.life_stage = LifeStage.ADOLESCENT
                        dispatch_life_event(evt, [character.gameobject])

                else:
                    if character.life_stage != LifeStage.CHILD:
                        character.life_stage = LifeStage.CHILD


class CharacterLifespanSystem(System):
    """Kills of characters who have reached their lifespan."""

    def on_update(self, world: World) -> None:
        for _, (character, age, life_span, _) in world.get_components(
            (Character, Age, Lifespan, Active)
        ):

            if age.value >= life_span.stat.value:
                Die(character.gameobject).execute()


class BusinessLifespanSystem(System):
    """Kills of business that have reached their lifespan."""

    def on_update(self, world: World) -> None:
        for _, (business, age, lifespan, _) in world.get_components(
            (Business, Age, Lifespan, Active)
        ):
            if age.value >= lifespan.stat.value and business.owner:
                CloseBusiness(business.gameobject).execute()


class ChildBirthSystem(System):
    """Spawns new children when pregnant characters reach their due dates."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDate)

        for _, (character, pregnancy, fertility, species, _) in world.get_components(
            (Character, Pregnant, Fertility, Species, Active)
        ):
            if pregnancy.due_date > current_date:
                continue

            other_parent = pregnancy.partner

            baby = create_child(
                birthing_parent=character.gameobject,
                other_parent=other_parent,
            )

            baby.add_component(
                ResidentOf(character.gameobject.get_component(ResidentOf).settlement)
            )

            household = character.gameobject.get_component(
                MemberOfHousehold
            ).household.get_component(Household)

            add_character_to_household(household, baby.get_component(Character))

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

            # Reduce the character's fertility according to their species
            fertility.stat.base_value -= species.species.fertility_cost_per_child

            have_child_evt = HaveChildEvent(
                character.gameobject,
                other_parent,
                baby,
            )
            dispatch_life_event(have_child_evt, [character.gameobject, other_parent])

            birth_evt = BirthEvent(baby)
            dispatch_life_event(birth_evt, [baby])


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

            for trait_instance in traits.traits.values():
                if not trait_instance.has_duration:
                    continue

                trait_instance.duration -= 1

                if trait_instance.duration <= 0:
                    traits_to_remove.append(trait_instance.trait)

            for trait_id in traits_to_remove:
                if relationship := traits.gameobject.try_component(Relationship):
                    remove_relationship_trait(
                        relationship.owner, relationship.target, trait_id
                    )
                else:
                    remove_trait(traits.gameobject, trait_id)
