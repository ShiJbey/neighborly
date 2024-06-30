"""Default systems to include into a simulation.

"""

import random
from collections import defaultdict
from typing import ClassVar, Optional

from neighborly.components.business import Business, BusinessStatus, JobRole, Occupation
from neighborly.components.character import (
    Character,
    Household,
    LifeStage,
    MemberOfHousehold,
    Pregnant,
    ResidentOf,
    Sex,
)
from neighborly.components.location import FrequentedLocations, Location
from neighborly.components.relationship import (
    IsMarried,
    KeyRelations,
    Relationships,
    Romance,
)
from neighborly.components.settlement import Settlement
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.components.stats import Sociability, Stats
from neighborly.config import SimulationConfig
from neighborly.ecs import Active, GameObject, System, World
from neighborly.helpers.action import get_action_probability
from neighborly.helpers.character import (
    add_character_to_household,
    create_household,
    remove_character_from_household,
    set_household_head,
)
from neighborly.helpers.relationship import (
    add_relationship,
    get_relationship,
    has_relationship,
)
from neighborly.libraries import JobRoleLibrary
from neighborly.plugins.actions import (
    BreakUp,
    Divorce,
    FireEmployee,
    FormCrush,
    GetMarried,
    GetPregnant,
    HireEmployee,
    PromoteEmployee,
    Retire,
    StartBusiness,
    StartDating,
)
from neighborly.simulation import Simulation


class FindJobSystem(System):
    """Unemployed characters try to find work."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        library = world.resources.get_resource(JobRoleLibrary)

        active_businesses = [
            business
            for _, (business, _) in world.get_components((Business, Active))
            if business.status == BusinessStatus.OPEN
        ]

        rng.shuffle(active_businesses)

        for _, (character_comp, _) in world.get_components((Character, Active)):
            character = character_comp.gameobject

            if character.has_component(Occupation):
                continue

            if character_comp.life_stage not in (
                LifeStage.YOUNG_ADULT,
                LifeStage.ADULT,
            ):
                continue

            potential_hires: list[HireEmployee] = []

            for business in active_businesses:
                open_positions = business.get_open_positions()

                for role_id in open_positions:
                    job_role = library.get_role(role_id)

                    if job_role.check_requirements(character):
                        action = HireEmployee(
                            business=business.gameobject,
                            character=character,
                            role=job_role,
                        )
                        potential_hires.append(action)

            if not potential_hires:
                continue

            action = rng.choice(potential_hires)

            action_probability = get_action_probability(action)

            if rng.random() < action_probability:
                action.execute()


class FiredFromJobSystem(System):
    """Occasionally fire an employee or two."""

    FIRING_THRESHOLD: ClassVar[float] = 0.8
    """Utility score required to consider someone for firing."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        # This loops through all the active businesses, scores the probability of
        # firing each of the current employees, and, if any are above the firing
        # threshold (class var), they are added to a list of potential employees
        # to fire.
        # The system selects one character at random from the list using weighted
        # random selection, and does a probability check on if the character will
        # actually be fired this time step.
        for _, (business, _) in world.get_components((Business, Active)):
            if business.status != BusinessStatus.OPEN:
                continue

            business_owner = business.owner

            if business_owner is None:
                continue

            potential_actions: list[tuple[FireEmployee, float]] = []
            action_utilities: list[float] = []

            # Evaluate firing each employee
            for employee, _ in business.employees.items():

                action = FireEmployee(business=business.gameobject, character=employee)
                action_probability = get_action_probability(action)

                if action_probability >= self.FIRING_THRESHOLD:
                    potential_actions.append((action, action_probability))
                    action_utilities.append(action_probability)

            if not potential_actions:
                continue

            chosen_action, action_probability = rng.choices(
                potential_actions, action_utilities, k=1
            )[0]

            if rng.random() < action_probability:
                chosen_action.execute()


class JobPromotionSystem(System):
    """Occasionally promote characters to higher positions at their jobs."""

    PROMOTION_THRESHOLD: ClassVar[float] = 0.8
    """Probability scored required to consider someone for a promotion."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)
        job_role_library = world.resources.get_resource(JobRoleLibrary)

        # Similar to firing characters, this systems loops through all the businesses
        # and scores the probability of promoting each of it's employees. Only employees
        # with probability scores above the threshold are considered. Once all employees
        # have been evaluated, one is selected randomly and we perform a "dice roll"
        # to see if they will actually be promoted this time step.
        for _, (business, _) in world.get_components((Business, Active)):
            if business.status != BusinessStatus.OPEN:
                continue

            business_owner = business.owner

            if business_owner is None:
                continue

            potential_promotions: list[tuple[PromoteEmployee, float]] = []
            potential_promotion_scores: list[float] = []

            # Evaluate promoting each employee
            for employee, current_role in business.employees.items():

                current_job_level = current_role.job_level

                open_positions = business.get_open_positions()

                for role_id in open_positions:
                    role = job_role_library.get_role(role_id)

                    if current_job_level >= role.job_level:
                        continue

                    action = PromoteEmployee(business_owner, employee, role)
                    probability_score = get_action_probability(action)

                    if probability_score > self.PROMOTION_THRESHOLD:
                        potential_promotions.append((action, probability_score))
                        potential_promotion_scores.append(probability_score)

            if not potential_promotions:
                continue

            action, action_probability = rng.choices(
                potential_promotions, potential_promotion_scores, k=1
            )[0]

            if rng.random() < action_probability:
                action.execute()


class StartBusinessSystem(System):
    """Characters have a chance of becoming a business owner."""

    @staticmethod
    def get_eligible_businesses(
        settlement: Settlement,
    ) -> list[tuple[str, GameObject, JobRole]]:
        """Get all potential businesses that could be built.

        Parameters
        ----------
        settlement
            The settlement where the business will be built.

        Returns
        -------
        tuple[str, GameObject, JobRole]
            The definition ID, district to build, and job role of eligible business
            definitions.
        """
        eligible_business_definitions: list[tuple[str, GameObject, JobRole]] = []
        weights: list[float] = []

        for district in settlement.districts:
            spawn_table = district.get_component(BusinessSpawnTable)

            for entry in spawn_table.table.values():
                if entry.instances >= entry.max_instances:
                    continue
                if entry.min_population >= settlement.population:
                    continue

                eligible_business_definitions.append(
                    (entry.definition_id, district, entry.owner_role)
                )
                weights.append(entry.spawn_frequency)

        return eligible_business_definitions

    def on_update(self, world: World) -> None:
        # This system loops through all the adult characters, giving them the option to
        # start a new business if:
        # (1) They meet the requirements for the owner role
        # (2) They are unemployed
        # (3) At least at the YOUNG_ADULT life stage
        # (4) They are residents of the settlement

        rng = world.resource_manager.get_resource(random.Random)

        for _, (character, resident_of, _) in world.get_components(
            (Character, ResidentOf, Active)
        ):
            if character.life_stage not in (LifeStage.YOUNG_ADULT, LifeStage.ADULT):
                continue

            if character.gameobject.has_component(Occupation):
                continue

            eligible_businesses = self.get_eligible_businesses(
                resident_of.settlement.get_component(Settlement)
            )

            actions: list[tuple[StartBusiness, float]] = []
            action_utilities: list[float] = []

            for definition_id, district, owner_role in eligible_businesses:

                if not owner_role.requirements:
                    action = StartBusiness(
                        character=character.gameobject,
                        business_definition_id=definition_id,
                        district=district,
                        owner_role=owner_role,
                    )
                    action_probability = get_action_probability(action)

                    if action_probability > 0:
                        actions.append((action, action_probability))
                        action_utilities.append(action_probability)

                else:
                    if owner_role.check_requirements(character.gameobject):
                        action = StartBusiness(
                            character=character.gameobject,
                            business_definition_id=definition_id,
                            district=district,
                            owner_role=owner_role,
                        )
                        action_probability = get_action_probability(action)

                        if action_probability > 0:
                            actions.append((action, action_probability))
                            action_utilities.append(action_probability)

            if not actions:
                continue

            action, action_probability = rng.choices(actions, action_utilities, k=1)[0]

            if rng.random() < action_probability:
                action.execute()


class CharacterDatingSystem(System):
    """Characters have a chance of dating their crush."""

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (character, key_relations, _) in world.get_components(
            (Character, KeyRelations, Active)
        ):
            if character.gameobject.has_component(IsMarried):
                continue

            potential_romances: list[tuple[StartDating, float]] = []
            potential_romance_scores: list[float] = []

            for partner in key_relations.get("crush"):

                if partner.has_component(IsMarried):
                    continue

                if partner == character.gameobject:
                    continue

                if partner.is_active is False:
                    continue

                if not partner.has_component(Character):
                    continue

                action = StartDating(character=character.gameobject, partner=partner)
                action_probability = get_action_probability(action)

                if action_probability > 0:
                    potential_romances.append((action, action_probability))
                    potential_romance_scores.append(action_probability)

            if not potential_romances:
                continue

            action, action_probability = rng.choices(
                potential_romances, potential_romance_scores, k=1
            )[0]

            if rng.random() < action_probability:
                action.execute()


class CharacterMarriageSystem(System):
    """Characters have a chance to get married"""

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (character, key_relations, _) in world.get_components(
            (Character, KeyRelations, Active)
        ):
            if character.gameobject.has_component(IsMarried):
                continue

            significant_others = key_relations.get("dating")

            potential_marriages: list[tuple[GetMarried, float]] = []
            potential_marriage_scores: list[float] = []

            for partner in significant_others:
                if partner.is_active is False:
                    continue

                if partner.has_component(IsMarried):
                    continue

                action = GetMarried(character=character.gameobject, partner=partner)
                action_probability = get_action_probability(action)

                if action_probability > 0:
                    potential_marriages.append((action, action_probability))
                    potential_marriage_scores.append(action_probability)

            if not potential_marriages:
                continue

            action, action_probability = rng.choices(
                potential_marriages, potential_marriage_scores, k=1
            )[0]

            if rng.random() < action_probability:
                action.execute()


class CharacterDivorceSystem(System):
    """Characters in marriages may choose to divorce their spouse."""

    def on_update(self, world: World) -> None:

        rng = world.resource_manager.get_resource(random.Random)

        for _, (character, key_relations, _) in world.get_components(
            (Character, KeyRelations, Active)
        ):

            spouses = key_relations.get("spouse")

            potential_divorces: list[tuple[Divorce, float]] = []
            potential_divorce_scores: list[float] = []

            for partner in spouses:

                if partner.is_active is False:
                    continue

                action = Divorce(character=character.gameobject, partner=partner)
                action_probability = get_action_probability(action)

                if action_probability > 0:
                    potential_divorces.append((action, action_probability))
                    potential_divorce_scores.append(action_probability)

            if not potential_divorces:
                continue

            action, action_probability = rng.choices(
                potential_divorces, potential_divorce_scores, k=1
            )[0]

            if rng.random() < action_probability:
                action.execute()


class DatingBreakUpSystem(System):
    """Characters in dating relationships may choose to break-up with their partner."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (character, key_relations, _) in world.get_components(
            (Character, KeyRelations, Active)
        ):

            partners = key_relations.get("dating")

            potential_break_ups: list[tuple[BreakUp, float]] = []
            potential_break_up_scores: list[float] = []

            if partners:
                partner = rng.choice(partners)

                if not partner.is_active:
                    continue

                action = BreakUp(
                    character=character.gameobject,
                    partner=partner,
                )
                action_probability = get_action_probability(action)

                if action_probability > 0:
                    potential_break_ups.append((action, action_probability))
                    potential_break_up_scores.append(action_probability)

            if not potential_break_ups:
                continue

            action, action_probability = rng.choices(
                potential_break_ups, potential_break_up_scores, k=1
            )[0]

            if rng.random() < action_probability:
                action.execute()


class PregnancySystem(System):
    """Female characters in marriages have a chance of getting pregnant."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (character, key_relations, _) in world.get_components(
            (Character, KeyRelations, Active)
        ):
            if character.sex != Sex.FEMALE:
                continue

            if character.gameobject.has_component(Pregnant):
                continue

            spouses = key_relations.get("spouse")

            potential_pregnancies: list[tuple[GetPregnant, float]] = []
            potential_pregnancy_scores: list[float] = []

            for partner in spouses:

                if partner.get_component(Character).sex != Sex.MALE:
                    continue

                if partner.is_active is False:
                    continue

                action = GetPregnant(character=character.gameobject, partner=partner)
                action_probability = get_action_probability(action)

                if action_probability > 0:
                    potential_pregnancies.append((action, action_probability))
                    potential_pregnancy_scores.append(action_probability)

            if not potential_pregnancies:
                continue

            action, action_probability = rng.choices(
                potential_pregnancies, potential_pregnancy_scores, k=1
            )[0]

            if rng.random() < action_probability:
                action.execute()


class RetirementSystem(System):
    """Senior characters working a job can consider if they want to retire."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (character, _, _) in world.get_components(
            (Character, Occupation, Active)
        ):
            if character.life_stage < LifeStage.SENIOR:
                continue

            if not character.gameobject.has_component(Occupation):
                continue

            action = Retire(character.gameobject)

            action_probability = get_action_probability(action)

            if rng.random() < action_probability:
                action.execute()


class AdultsFormOwnHouseholdSystem(System):
    """Characters may chose to start their own households.

    Adult characters who are not the head or spouse of a household, may start their own
    households.
    """

    def on_update(self, world: World) -> None:
        for _, (character, member_of_household, _) in world.get_components(
            (Character, MemberOfHousehold, Active)
        ):
            if character.life_stage < LifeStage.YOUNG_ADULT:
                continue

            household = member_of_household.household.get_component(Household)

            if not character.gameobject != household.head:
                continue

            new_household = create_household(world).get_component(Household)
            set_household_head(new_household.gameobject, character.gameobject)
            remove_character_from_household(household.gameobject, character.gameobject)
            add_character_to_household(new_household.gameobject, character.gameobject)


class CrushFormationSystem(System):
    """Every timestep there is a possibility that a character might form a new crush.

    This system is intended to assist with romantic depth within the simulation. It adds
    an additional layer of nuance to relationships since characters might form crushes
    on characters that they are not currently in a romantic relationship with.
    """

    __slots__ = ("crush_threshold",)

    crush_threshold: float
    """Probability score required for someone to form a crush."""

    def __init__(self, crush_threshold: float = 0.6) -> None:
        super().__init__()
        self.crush_threshold = crush_threshold

    def on_add(self, world: World) -> None:
        config = world.resources.get_resource(SimulationConfig)

        if threshold := config.settings.get("crush_threshold"):
            self.crush_threshold = float(threshold)

    def on_update(self, world: World) -> None:
        # 1) Loop through all the active characters
        # 2) Get their outgoing relationships
        # 3) Find the person that they have the highest romantic attraction to
        # 4) Run a probability check
        # 5) If successful, add a crush trait to the relationship and remove any
        #    existing crushes.

        rng = world.resources.get_resource(random.Random)

        for _, (character, key_relations, relationships, _) in world.get_components(
            (Character, KeyRelations, Relationships, Active)
        ):
            current_crush: Optional[GameObject] = None
            potential_crush: Optional[GameObject] = None
            highest_romance: float = 0

            crushes = key_relations.get("crush")
            if crushes:
                current_crush = crushes[0]
                potential_crush = current_crush
                highest_romance = (
                    get_relationship(character.gameobject, potential_crush)
                    .get_component(Stats)
                    .get_stat("romance")
                    .value
                )

            for target, relationship in relationships.outgoing.items():

                if target == character.gameobject:
                    continue

                if not target.is_active:
                    continue

                romance = relationship.get_component(Romance).stat.value

                if romance > highest_romance:
                    highest_romance = romance
                    potential_crush = target

            if potential_crush is None or potential_crush == current_crush:
                continue

            action = FormCrush(character=character.gameobject, crush=potential_crush)

            action_probability = get_action_probability(action)

            if action_probability < self.crush_threshold:
                continue

            if rng.random() < action_probability:
                action.execute()


class MeetNewPeopleSystem(System):
    """Characters introduce themselves to new people that frequent the same places.

    Notes
    -----
    This system uses a character's sociability stat score to determine the probability
    of them introducing themselves to someone else. The goal is for characters with
    higher sociability scores to form more relationships over the course of their lives.
    """

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (
            character,
            frequented_locations,
            sociability,
            _,
        ) in world.get_components(
            (Character, FrequentedLocations, Sociability, Active)
        ):
            probability_meet_someone = sociability.stat.normalized

            if rng.random() < probability_meet_someone:
                candidate_scores: defaultdict[GameObject, int] = defaultdict(int)

                for loc in frequented_locations:
                    for other in loc.get_component(Location).frequented_by:
                        if other != character.gameobject and not has_relationship(
                            character.gameobject, other
                        ):
                            candidate_scores[other] += 1

                if candidate_scores:
                    rng = world.resource_manager.get_resource(random.Random)

                    acquaintance = rng.choices(
                        list(candidate_scores.keys()),
                        weights=list(candidate_scores.values()),
                        k=1,
                    )[0]

                    if (
                        rng.random()
                        < acquaintance.get_component(Sociability).stat.normalized
                    ):
                        add_relationship(character.gameobject, acquaintance)
                        add_relationship(acquaintance, character.gameobject)


def load_plugin(sim: Simulation) -> None:
    """Load systems into the simulation."""

    sim.world.systems.add_system(FindJobSystem())
    sim.world.systems.add_system(FiredFromJobSystem())
    sim.world.systems.add_system(JobPromotionSystem())
    sim.world.systems.add_system(StartBusinessSystem())
    sim.world.systems.add_system(CharacterDatingSystem())
    sim.world.systems.add_system(CharacterMarriageSystem())
    sim.world.systems.add_system(CharacterDivorceSystem())
    sim.world.systems.add_system(DatingBreakUpSystem())
    sim.world.systems.add_system(PregnancySystem())
    sim.world.systems.add_system(RetirementSystem())
    # sim.world.systems.add_system(AdultsFormOwnHouseholdSystem())
    sim.world.systems.add_system(CrushFormationSystem())
    sim.world.systems.add_system(MeetNewPeopleSystem())
