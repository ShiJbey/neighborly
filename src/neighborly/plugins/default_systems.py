from __future__ import annotations

import random
from collections import defaultdict
from typing import cast

from neighborly.components.business import Business, BusinessStatus
from neighborly.components.character import (
    Character,
    Household,
    LifeStage,
    MemberOfHousehold,
    Pregnant,
    ResidentOf,
    Sex,
    Species,
)
from neighborly.components.location import (
    CurrentSettlement,
    FrequentedLocations,
    Location,
    LocationPreferences,
)
from neighborly.components.relationship import KeyRelations
from neighborly.components.settlement import District, Settlement
from neighborly.components.shared import Age
from neighborly.components.spawn_table import CharacterSpawnTable, DistrictSpawnTable
from neighborly.components.stats import Fertility, Lifespan
from neighborly.config import SimulationConfig
from neighborly.datetime import MONTHS_PER_YEAR, SimDate
from neighborly.definitions import DistrictDef
from neighborly.ecs import Active, Event, GameObject, System, World
from neighborly.helpers.character import (
    add_character_to_household,
    create_character,
    create_child,
    create_household,
    remove_character_from_household,
    set_household_head,
)
from neighborly.helpers.content_selection import get_with_tags
from neighborly.helpers.location import score_location
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.settlement import (
    add_character_to_settlement,
    add_district_to_settlement,
    create_district,
    create_settlement,
)
from neighborly.helpers.traits import add_trait_with_id, has_trait
from neighborly.libraries import DistrictLibrary, SettlementLibrary
from neighborly.life_event import dispatch_life_event
from neighborly.plugins.actions import CloseBusiness, Die
from neighborly.plugins.default_events import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeSeniorEvent,
    BecomeYoungAdultEvent,
    BirthEvent,
    ChildBirthEvent,
    DeathEvent,
    JoinSettlementEvent,
    SettlementAddedEvent,
)
from neighborly.simulation import Simulation


class InitializeSettlementSystem(System):
    """Creates one or more settlement instances using simulation config settings."""

    __system_group__ = "InitializationSystems"
    __update_order__ = ("last",)

    __slots__ = ("num_districts", "min_businesses_capacity", "max_business_capacity")

    num_districts: int
    min_business_capacity: int
    max_business_capacity: int

    def __init__(
        self,
        num_districts: int = 4,
        min_business_capacity: int = 2,
        max_business_capacity: int = 10,
    ) -> None:
        super().__init__()
        self.num_districts = num_districts
        self.min_business_capacity = min_business_capacity
        self.max_business_capacity = max_business_capacity

    def on_add(self, world: World) -> None:
        config = world.resources.get_resource(SimulationConfig)

        if num_districts := config.settings.get("num_districts"):
            self.num_districts = int(num_districts)

        if min_business_capacity := config.settings.get("min_business_capacity"):
            self.min_business_capacity = int(min_business_capacity)

        if max_business_capacity := config.settings.get("max_business_capacity"):
            self.max_business_capacity = int(max_business_capacity)

    def on_update(self, world: World) -> None:
        config = world.resource_manager.get_resource(SimulationConfig)

        rng = world.resource_manager.get_resource(random.Random)

        settlement_library = world.resources.get_resource(SettlementLibrary)
        district_library = world.resources.get_resource(DistrictLibrary)

        # Select a settlement from the library using the theme tags
        selection_tags = [f"~{tag}" for tag in config.settings.get("theme_tags", [])]

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

        n_districts_remaining = self.num_districts

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

            district.business_capacity = rng.randint(
                self.min_business_capacity, self.max_business_capacity
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

    __slots__ = ("growth_factor",)

    growth_factor: float

    def __init__(self, growth_factor: float = 0.4) -> None:
        super().__init__()
        self.growth_factor = growth_factor

    def on_add(self, world: World) -> None:
        config = world.resources.get_resource(SimulationConfig)

        if growth_factor := config.settings.get("growth_factor"):
            self.growth_factor = float(growth_factor)

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        # Find vacant residences
        for _, (_, current_settlement, spawn_table, _) in world.get_components(
            (District, CurrentSettlement, CharacterSpawnTable, Active)
        ):
            if len(spawn_table.table) == 0:
                continue

            if rng.random() > self.growth_factor:
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

            character = create_character(world, character_definition_id).get_component(
                Character
            )

            household = create_household(world).get_component(Household)

            set_household_head(household.gameobject, character.gameobject)
            add_character_to_household(household.gameobject, character.gameobject)

            add_character_to_settlement(
                current_settlement.settlement.get_component(Settlement), character
            )

            world.events.dispatch_event(
                Event("character-added", world=world, character=character)
            )

            event = JoinSettlementEvent(
                character.gameobject,
                current_settlement.settlement,
            )

            dispatch_life_event(event, [character.gameobject])


class HouseholdSystem(System):
    """Handles household logistics.

    This class handles:
    - Creating new households for spawned characters.
    - Removing characters from households upon their death.
    - Appointing family heads when the head dies.
    """

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        return

    def on_add(self, world: World) -> None:
        world.events.on_event("household-added", self.handle_household_added)

    def handle_household_added(self, event: Event) -> None:
        """Registers event listeners with new households."""

        household: GameObject = event.data["household"]

        household.add_event_listener("member-added", self.handle_member_added)
        household.add_event_listener("member-removed", self.handle_member_removed)

    def handle_member_added(self, event: Event) -> None:
        """Handle when a member is added to a family."""

        character: GameObject = event.data["character"]

        character.add_event_listener("death", self.handle_member_death)

    def handle_member_removed(self, event: Event) -> None:
        """Handle when a member is removed from a family."""

        character: GameObject = event.data["character"]

        character.remove_event_listener("death", self.handle_member_death)

    @staticmethod
    def handle_member_death(event: Event) -> None:
        """Removes characters from the household when they die."""

        death_event = cast(DeathEvent, event)
        character = death_event.character.get_component(Character)

        household = character.gameobject.get_component(
            MemberOfHousehold
        ).household.get_component(Household)

        was_household_head = character.gameobject == household.head

        remove_character_from_household(household.gameobject, character.gameobject)

        if was_household_head:
            set_household_head(household.gameobject, None)

            if not household.members:
                household.gameobject.destroy()
                return

            # appoint new head
            spouse_appointed = False
            for member in household.members:
                rel_to_member = get_relationship(character.gameobject, member)
                if has_trait(rel_to_member, "spouse"):
                    set_household_head(household.gameobject, member)
                    spouse_appointed = True
                    break

            if not spouse_appointed:
                # appoint oldest member
                members = sorted(
                    [(m.get_component(Age).value, m) for m in household.members],
                    key=lambda e: e[0],
                )

                set_household_head(household.gameobject, members[-1][1])


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

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        # This system runs every simulated month
        elapsed_years: float = 1.0 / MONTHS_PER_YEAR

        for _, (age, _) in world.get_components((Age, Active)):
            age.value += elapsed_years


class LifeStageSystem(System):
    """Updates the life stage of all characters to reflect their current age."""

    __system_group__ = "EarlyUpdateSystems"

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

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (character, age, life_span, _) in world.get_components(
            (Character, Age, Lifespan, Active)
        ):

            if age.value >= life_span.stat.value:
                Die(character.gameobject).execute()


class BusinessLifespanSystem(System):
    """Kills of business that have reached their lifespan."""

    __system_group__ = "EarlyUpdateSystems"

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

            household = character.gameobject.get_component(MemberOfHousehold).household

            add_character_to_household(household, baby)

            # Birthing parent to child
            add_trait_with_id(get_relationship(character.gameobject, baby), "child")
            add_trait_with_id(get_relationship(baby, character.gameobject), "parent")
            add_trait_with_id(
                get_relationship(baby, character.gameobject), "biological_parent"
            )
            character.gameobject.get_component(KeyRelations).set("child", baby)
            baby.get_component(KeyRelations).set("parent", character.gameobject)

            # Other parent to child
            add_trait_with_id(get_relationship(other_parent, baby), "child")
            add_trait_with_id(get_relationship(baby, other_parent), "parent")
            add_trait_with_id(get_relationship(baby, other_parent), "biological_parent")
            other_parent.get_component(KeyRelations).set("child", baby)
            baby.get_component(KeyRelations).set("parent", other_parent)

            # Create relationships with children of birthing parent
            for child in character.gameobject.get_component(KeyRelations).get("child"):
                if child == baby:
                    continue

                # Baby to sibling
                add_trait_with_id(get_relationship(baby, child), "sibling")
                add_trait_with_id(get_relationship(child, baby), "sibling")
                baby.get_component(KeyRelations).set("sibling", child)
                child.get_component(KeyRelations).set("sibling", baby)

            # Create relationships with children of other parent
            for child in other_parent.get_component(KeyRelations).get("child"):
                if child == baby:
                    continue

                # Baby to sibling
                add_trait_with_id(get_relationship(baby, child), "sibling")
                add_trait_with_id(get_relationship(child, baby), "sibling")
                baby.get_component(KeyRelations).set("sibling", child)
                child.get_component(KeyRelations).set("sibling", baby)

            character.gameobject.remove_component(Pregnant)

            # Reduce the character's fertility according to their species
            fertility.stat.base_value -= species.species.fertility_cost_per_child

            child_birth_evt = ChildBirthEvent(
                character.gameobject,
                other_parent,
                baby,
            )
            dispatch_life_event(child_birth_evt, [character.gameobject, other_parent])

            birth_evt = BirthEvent(baby)
            dispatch_life_event(birth_evt, [baby])


def load_plugin(sim: Simulation) -> None:
    """Load systems into the simulation."""

    sim.world.systems.add_system(InitializeSettlementSystem())
    sim.world.systems.add_system(SpawnNewResidentSystem())
    sim.world.systems.add_system(HouseholdSystem())
    sim.world.systems.add_system(UpdateFrequentedLocationSystem())
    sim.world.systems.add_system(AgingSystem())
    sim.world.systems.add_system(LifeStageSystem())
    sim.world.systems.add_system(CharacterLifespanSystem())
    sim.world.systems.add_system(BusinessLifespanSystem())
    sim.world.systems.add_system(ChildBirthSystem())
