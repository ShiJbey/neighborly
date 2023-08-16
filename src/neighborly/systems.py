import math
import random
from collections import defaultdict
from typing import ClassVar, DefaultDict, List, Tuple

from neighborly.ai.brain import AIBrain, Goals
from neighborly.components.business import (
    Business,
    InTheWorkforce,
    Occupation,
    OpenForBusiness,
    Services,
    Unemployed,
)
from neighborly.components.character import (
    CanAge,
    CanGetOthersPregnant,
    CanGetPregnant,
    CharacterCreatedEvent,
    ChildOf,
    Dating,
    Family,
    Fertility,
    FertilityDecay,
    GameCharacter,
    Health,
    HealthDecay,
    HealthDecayChance,
    LifeStage,
    LifeStageType,
    Married,
    ParentOf,
    Pregnant,
    SiblingOf,
    Sociability,
)
from neighborly.components.residence import Residence, Resident, set_residence
from neighborly.components.shared import (
    Age,
    FrequentedBy,
    FrequentedLocations,
    Lifespan,
    Location,
)
from neighborly.ecs import Active, GameObject, System, SystemGroup, World
from neighborly.events import (
    BecameAcquaintancesEvent,
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeSeniorEvent,
    BecomeYoungAdultEvent,
    BirthEvent,
    GetPregnantEvent,
    HaveChildEvent,
)
from neighborly.goals import (
    BreakUp,
    DepartSimulation,
    FindEmployment,
    FindOwnPlace,
    FindRomance,
    GetDivorced,
    GetMarried,
    Retire,
)
from neighborly.life_event import RandomLifeEventLibrary
from neighborly.location_preference import LocationPreferenceRuleLibrary
from neighborly.relationship import (
    Friendship,
    InteractionScore,
    PlatonicCompatibility,
    Relationship,
    Relationships,
    Romance,
    RomanticCompatibility,
    SocialRuleLibrary,
    add_relationship,
    get_relationship,
    get_relationships_with_components,
    has_relationship,
)
from neighborly.roles import Roles
from neighborly.stats import StatModifier, StatModifierType
from neighborly.time import SimDateTime
from neighborly.utils.common import (
    die,
    get_random_child_character_type,
    is_employed,
    shutdown_business,
)
from neighborly.utils.query import is_single

############################################
#              SYSTEM GROUPS               #
############################################


class InitializationSystemGroup(SystemGroup):
    """A group of systems that run once at the beginning of the simulation.

    Any content initialization systems or initial world building systems should
    belong to this group.
    """

    def on_update(self, world: World) -> None:
        # Run all child systems first before deactivating
        super().on_update(world)
        self.set_active(False)


class EarlyUpdateSystemGroup(SystemGroup):
    """The early phase of the update loop."""

    pass


class UpdateSystemGroup(SystemGroup):
    """The main phase of the update loop."""

    pass


class LateUpdateSystemGroup(SystemGroup):
    """The late phase of the update loop."""

    pass


class RelationshipUpdateSystemGroup(SystemGroup):
    """System group for updating relationship components.

    If there are components that should grow or decay over time, their systems
    should be added to this group.
    """

    pass


class StatusUpdateSystemGroup(SystemGroup):
    """System group for updating status components."""

    pass


class GoalSuggestionSystemGroup(SystemGroup):
    """System group for suggesting Goals to characters"""

    pass


class DataCollectionSystemGroup(SystemGroup):
    """System group for collecting data.

    Any system that collects data during the course of the simulation should
    belong to this group.
    """

    pass


############################################
#        SYSTEMS ACTIVE BY DEFAULT         #
############################################


class TimeSystem(System):
    """Advances the current date of the simulation."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDateTime)
        current_date.increment(years=1)


class RandomLifeEventSystem(System):
    """Attempts to execute non-optional life events

    Life events triggered by this system do not pass through the character AI. You can
    consider these events as the simulation making an authoritative decision that
    something is going to happen, checking the preconditions, and finally making it so.

    It is the simplest form of narrative content creation in the simulation since you
    do not need to worry about characters approving of life event before they are
    allowed to take place.
    """

    def on_update(self, world: World) -> None:
        """Simulate LifeEvents for characters"""
        rng = world.resource_manager.get_resource(random.Random)
        event_library = world.resource_manager.get_resource(RandomLifeEventLibrary)

        total_population = len(world.get_components((GameCharacter, Active)))

        if len(event_library) == 0:
            return

        for _ in range(total_population // 2):
            event_type = event_library.pick_one(rng)
            if event := event_type.instantiate(world):
                if rng.random() < event.get_probability():
                    event.dispatch()


class MeetNewPeopleSystem(System):
    """Characters meet new people based on places they frequent"""

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for gid, (_, _, frequented_locations, sociability) in world.get_components(
            (GameCharacter, Active, FrequentedLocations, Sociability)
        ):
            character = world.gameobject_manager.get_gameobject(gid)

            probability_meet_someone = float(sociability.value / 255)

            if rng.random() > probability_meet_someone:
                # Do not meet someone if the probability score does not pass
                continue

            candidate_scores: DefaultDict[GameObject, int] = defaultdict(int)

            for loc in frequented_locations:
                for other in loc.get_component(FrequentedBy):
                    if other != character and not has_relationship(character, other):
                        candidate_scores[other] += 1

            if candidate_scores:
                rng = world.resource_manager.get_resource(random.Random)

                acquaintance = rng.choices(
                    list(candidate_scores.keys()),
                    weights=list(candidate_scores.values()),
                    k=1,
                )[0]

                add_relationship(character, acquaintance)
                add_relationship(acquaintance, character)

                # Calculate interaction scores
                get_relationship(character, acquaintance).get_component(
                    InteractionScore
                ).base_value += candidate_scores[acquaintance]

                get_relationship(acquaintance, character).get_component(
                    InteractionScore
                ).base_value += candidate_scores[acquaintance]

                BecameAcquaintancesEvent(
                    world,
                    world.resource_manager.get_resource(SimDateTime).copy(),
                    character,
                    acquaintance,
                ).dispatch()


class IncrementAgeSystem(System):
    """Increases the age of all active GameObjects with Age components."""

    def on_update(self, world: World) -> None:
        for _, (age, _) in world.get_components((Age, Active)):
            age.value += 1


class HealthDecaySystem(System):
    """Decay the health points of characters as they get older."""

    DECAY_CHANCE_INCREASE: ClassVar[float] = 0.02
    STARTING_DECAY_CHANCE: ClassVar[float] = 0.07

    def on_add(self, world: World) -> None:
        world.event_manager.on_event(
            CharacterCreatedEvent, HealthDecaySystem.add_health_decay_to_character
        )

        world.event_manager.on_event(
            BecomeYoungAdultEvent, HealthDecaySystem.add_health_decay_to_new_adult
        )

    @staticmethod
    def add_health_decay_to_character(event: CharacterCreatedEvent) -> None:
        life_stage = event.character.get_component(LifeStage).life_stage

        if life_stage <= LifeStageType.Adolescent:
            return

        character_config = event.character.get_component(
            GameCharacter
        ).character_type.config

        event.character.get_component(HealthDecay).add_modifier(
            StatModifier(
                character_config.base_health_decay, modifier_type=StatModifierType.Flat
            )
        )

        aging_config = character_config.aging

        if aging_config is None:
            return

        character_age = event.character.get_component(Age)

        if life_stage == LifeStageType.YoungAdult:
            event.character.get_component(
                HealthDecayChance
            ).base_value = HealthDecaySystem.STARTING_DECAY_CHANCE + (
                HealthDecaySystem.DECAY_CHANCE_INCREASE
                * (character_age.value - aging_config.young_adult_age)
            )

        elif life_stage == LifeStageType.Adult:
            event.character.get_component(
                HealthDecayChance
            ).base_value = HealthDecaySystem.STARTING_DECAY_CHANCE + (
                HealthDecaySystem.DECAY_CHANCE_INCREASE
                * (character_age.value - aging_config.adult_age)
            )

        elif life_stage == LifeStageType.Senior:
            event.character.get_component(
                HealthDecayChance
            ).base_value = HealthDecaySystem.STARTING_DECAY_CHANCE + (
                HealthDecaySystem.DECAY_CHANCE_INCREASE
                * (character_age.value - aging_config.senior_age)
            )

    @staticmethod
    def add_health_decay_to_new_adult(event: BecomeYoungAdultEvent) -> None:
        character_config = event.character.get_component(
            GameCharacter
        ).character_type.config

        event.character.get_component(HealthDecay).add_modifier(
            StatModifier(
                character_config.base_health_decay, modifier_type=StatModifierType.Flat
            )
        )

        aging_config = character_config.aging

        if aging_config is None:
            return

        event.character.get_component(
            HealthDecayChance
        ).base_value = HealthDecaySystem.STARTING_DECAY_CHANCE

    def on_update(self, world: World) -> None:
        for _, (
            _,
            health,
            health_decay,
            decay_chance,
            life_stage,
        ) in world.get_components(
            (Active, Health, HealthDecay, HealthDecayChance, LifeStage)
        ):
            if life_stage.life_stage >= LifeStageType.YoungAdult:
                decay_chance.base_value += HealthDecaySystem.DECAY_CHANCE_INCREASE

            if random.random() <= decay_chance.value:
                health.base_value += health_decay.value


class UpdateLifeStageSystem(System):
    """Change the life stage of a character based on it's age a life stage config."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, (
            game_character,
            age,
            life_stage,
            _,
            _,
        ) in world.get_components((GameCharacter, Age, LifeStage, CanAge, Active)):
            character = world.gameobject_manager.get_gameobject(guid)

            aging_config = game_character.character_type.config.aging

            if aging_config is None:
                continue

            if age.value >= aging_config.senior_age:
                if life_stage.life_stage != LifeStageType.Senior:
                    life_stage.life_stage = LifeStageType.Senior
                    BecomeSeniorEvent(world, current_date, character).dispatch()

            elif age.value >= aging_config.adult_age:
                if life_stage.life_stage != LifeStageType.Adult:
                    life_stage.life_stage = LifeStageType.Adult
                    BecomeAdultEvent(world, current_date, character).dispatch()

            elif age.value >= aging_config.young_adult_age:
                if life_stage.life_stage != LifeStageType.YoungAdult:
                    life_stage.life_stage = LifeStageType.YoungAdult
                    BecomeYoungAdultEvent(world, current_date, character).dispatch()

            elif age.value >= aging_config.adolescent_age:
                if life_stage.life_stage != LifeStageType.Adolescent:
                    life_stage.life_stage = LifeStageType.Adolescent
                    BecomeAdolescentEvent(world, current_date, character).dispatch()

            else:
                if life_stage.life_stage != LifeStageType.Child:
                    life_stage.life_stage = LifeStageType.Child


class FertilityDecaySystem(System):
    @staticmethod
    def update_young_adult_fertility(event: BecomeYoungAdultEvent) -> None:
        if event.character.has_component(CanGetPregnant):
            event.character.get_component(Fertility).base_value = 1.0
        elif event.character.has_component(CanGetOthersPregnant):
            event.character.get_component(Fertility).base_value = 1.0

    @staticmethod
    def update_adult_fertility(event: BecomeAdultEvent) -> None:
        if event.character.has_component(CanGetPregnant):
            event.character.get_component(Fertility).base_value = 0.7
        elif event.character.has_component(CanGetOthersPregnant):
            event.character.get_component(Fertility).base_value = 0.9

    @staticmethod
    def update_senior_fertility(event: BecomeSeniorEvent) -> None:
        if event.character.has_component(CanGetPregnant):
            event.character.get_component(Fertility).base_value = 0
        elif event.character.has_component(CanGetOthersPregnant):
            event.character.get_component(Fertility).base_value = 0.5

    def on_add(self, world: World) -> None:
        world.event_manager.on_event(
            BecomeYoungAdultEvent, FertilityDecaySystem.update_young_adult_fertility
        )
        world.event_manager.on_event(
            BecomeAdultEvent, FertilityDecaySystem.update_adult_fertility
        )
        world.event_manager.on_event(
            BecomeSeniorEvent, FertilityDecaySystem.update_senior_fertility
        )

    def on_update(self, world: World) -> None:
        for _, (_, fertility, fertility_decay, life_stage) in world.get_components(
            (Active, Fertility, FertilityDecay, LifeStage)
        ):
            if life_stage.life_stage >= LifeStageType.Adult:
                fertility.base_value -= fertility_decay.value


class EmploymentSystem(System):
    """Provides unemployed characters with a goal to find employment."""

    __slots__ = "years_to_find_a_job"

    years_to_find_a_job: int
    """The number of year characters can look for a job before considering departure."""

    def __init__(self, years_to_find_a_job: int = 5) -> None:
        super().__init__()
        self.years_to_find_a_job = years_to_find_a_job

    @staticmethod
    def on_adult_join_settlement(event: CharacterCreatedEvent) -> None:
        if (
            event.character.has_component(Active)
            and event.character.get_component(LifeStage).life_stage
            >= LifeStageType.YoungAdult
        ):
            date = event.world.resource_manager.get_resource(SimDateTime)
            event.character.add_component(InTheWorkforce, timestamp=date.year)

            if roles := event.character.try_component(Roles):
                if len(roles.get_roles_of_type(Occupation)) == 0:
                    event.character.add_component(Unemployed, timestamp=date.year)

    @staticmethod
    def join_workforce_when_young_adult(event: BecomeYoungAdultEvent) -> None:
        date = event.world.resource_manager.get_resource(SimDateTime)
        event.character.add_component(InTheWorkforce, timestamp=date.year)

        if roles := event.character.try_component(Roles):
            if len(roles.get_roles_of_type(Occupation)) == 0:
                event.character.add_component(Unemployed, timestamp=date.year)

    def on_add(self, world: World) -> None:
        world.event_manager.on_event(
            CharacterCreatedEvent, EmploymentSystem.on_adult_join_settlement
        )

        world.event_manager.on_event(
            BecomeYoungAdultEvent, EmploymentSystem.join_workforce_when_young_adult
        )

    def on_update(self, world: World) -> None:
        current_year: int = world.resource_manager.get_resource(SimDateTime).year
        for guid, (unemployed, _) in world.get_components((Unemployed, Active)):
            character = world.gameobject_manager.get_gameobject(guid)

            years_unemployed = current_year - unemployed.timestamp

            # Keep trying to find a job
            find_employment_goal = FindEmployment(character)
            priority = find_employment_goal.get_utility()[character]
            character.get_component(Goals).push_goal(priority, find_employment_goal)

            # Start thinking about leaving the settlement
            if years_unemployed > self.years_to_find_a_job:
                spousal_relationships = get_relationships_with_components(
                    character, Married
                )

                # They should depart if they have no spouse(s)
                if len(spousal_relationships) == 0:
                    depart_goal = DepartSimulation(character)
                    priority = depart_goal.get_utility()[character]
                    character.get_component(Goals).push_goal(priority, depart_goal)

                # Depart if none of their spouses has a job either
                if not any(
                    [
                        is_employed(rel.get_component(Relationship).target)
                        for rel in spousal_relationships
                    ]
                ):
                    depart_goal = DepartSimulation(character)
                    priority = depart_goal.get_utility()[character]
                    character.get_component(Goals).push_goal(priority, depart_goal)


class ChildBirthSystem(System):
    """Handles childbirths for pregnant characters."""

    FERTILITY_LOSS_AFTER_BIRTH = 0.7

    def on_update(self, world: World) -> None:
        date = world.resource_manager.get_resource(SimDateTime)

        for guid, pregnant in world.get_component(Pregnant):
            pregnant_character = world.gameobject_manager.get_gameobject(guid)

            if date.year <= pregnant.timestamp:
                continue

            other_parent = pregnant.partner

            child_character_type = get_random_child_character_type(
                pregnant_character, other_parent
            )

            baby = child_character_type.instantiate(
                world=world,
                last_name=pregnant_character.get_component(GameCharacter).last_name,
            )

            set_residence(
                baby,
                pregnant_character.get_component(Resident).residence,
            )

            # Birthing parent to child
            add_relationship(pregnant_character, baby)
            get_relationship(pregnant_character, baby).add_component(
                ParentOf, timestamp=date.year
            )

            get_relationship(pregnant_character, baby).add_component(
                Family, timestamp=date.year
            )

            # Child to birthing parent
            add_relationship(baby, pregnant_character)
            get_relationship(baby, pregnant_character).add_component(
                ChildOf, timestamp=date.year
            )
            get_relationship(baby, pregnant_character).add_component(
                Family, timestamp=date.year
            )

            # Other parent to child
            add_relationship(other_parent, baby)
            get_relationship(other_parent, baby).add_component(
                ParentOf, timestamp=date.year
            )
            get_relationship(other_parent, baby).add_component(
                Family, timestamp=date.year
            )

            # Child to other parent
            add_relationship(baby, other_parent)
            get_relationship(baby, other_parent).add_component(
                ChildOf, timestamp=date.year
            )
            get_relationship(baby, other_parent).add_component(
                Family, timestamp=date.year
            )

            # Create relationships with children of birthing parent
            for relationship in get_relationships_with_components(
                pregnant_character, ParentOf
            ):
                rel = relationship.get_component(Relationship)

                if rel.target == baby:
                    continue

                sibling = rel.target

                # Baby to sibling
                add_relationship(baby, sibling)
                get_relationship(baby, sibling).add_component(
                    SiblingOf, timestamp=date.year
                )
                get_relationship(baby, sibling).add_component(
                    Family, timestamp=date.year
                )

                # Sibling to baby
                add_relationship(sibling, baby)
                get_relationship(sibling, baby).add_component(
                    SiblingOf, timestamp=date.year
                )
                get_relationship(sibling, baby).add_component(
                    Family, timestamp=date.year
                )

            # Create relationships with children of other parent
            for relationship in get_relationships_with_components(
                other_parent, ParentOf
            ):
                rel = relationship.get_component(Relationship)
                if rel.target == baby:
                    continue

                sibling = rel.target

                # Baby to sibling
                add_relationship(baby, sibling)
                get_relationship(baby, sibling).add_component(
                    SiblingOf, timestamp=date.year
                )
                get_relationship(baby, sibling).add_component(
                    Family, timestamp=date.year
                )

                # Sibling to baby
                add_relationship(sibling, baby)
                get_relationship(sibling, baby).add_component(
                    SiblingOf, timestamp=date.year
                )
                get_relationship(sibling, baby).add_component(
                    Family, timestamp=date.year
                )

            pregnant_character.remove_component(Pregnant)
            pregnant_character.get_component(
                Fertility
            ).base_value -= ChildBirthSystem.FERTILITY_LOSS_AFTER_BIRTH

            # Pregnancy event dates are retro-fit to be the actual date that the
            # child was due.
            have_child_event = HaveChildEvent(
                world, date, pregnant_character, other_parent, baby
            )
            birth_event = BirthEvent(world, date, baby)

            world.event_manager.dispatch_event(have_child_event)
            world.event_manager.dispatch_event(birth_event)


class EvaluateSocialRulesSystem(System):
    """Evaluates social rules against existing relationships

    This system reevaluates social rules on characters' relationships and updates the
    active modifiers. This system exists because we may need to update relationships to
    reflect new components or relationship statuses that were not present during the
    last social rule evaluation.
    """

    def on_update(self, world: World) -> None:
        rule_library = world.resource_manager.get_resource(SocialRuleLibrary)

        for guid, (relationship, _) in world.get_components((Relationship, Active)):
            relationship_obj = world.gameobject_manager.get_gameobject(guid)

            # Remove the affects of existing rules
            for rule in relationship.iter_active_rules():
                rule.remove(relationship.owner, relationship.target, relationship_obj)
            relationship.clear_active_rules()

            # Test all the rules in the library and apply those with passing
            # preconditions
            for rule in rule_library.iter_rules():
                if rule.check_preconditions(
                    relationship.owner, relationship.target, relationship_obj
                ):
                    rule.apply(
                        relationship.owner, relationship.target, relationship_obj
                    )
                    relationship.add_rule(rule)


class PassiveFriendshipChange(System):
    """Friendship stats have a probability of changing each time step."""

    CHANCE_OF_CHANGE: ClassVar[float] = 0.20

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (
            _,
            friendship,
            compatibility,
            interaction_score,
            _,
        ) in world.get_components(
            (Relationship, Friendship, PlatonicCompatibility, InteractionScore, Active)
        ):
            final_chance = (
                PassiveFriendshipChange.CHANCE_OF_CHANGE * interaction_score.value
            )

            if rng.random() < final_chance:
                friendship.base_value = friendship.base_value + compatibility.value


class PassiveRomanceChange(System):
    """Romance stats have a probability of changing each time step."""

    CHANCE_OF_CHANGE: ClassVar[float] = 0.20

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (
            _,
            romance,
            compatibility,
            interaction_score,
            _,
        ) in world.get_components(
            (Relationship, Romance, RomanticCompatibility, InteractionScore, Active)
        ):
            final_chance = (
                PassiveRomanceChange.CHANCE_OF_CHANGE * interaction_score.value
            )

            if rng.random() < final_chance:
                romance.base_value = romance.base_value + compatibility.value


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

    @staticmethod
    def score_location(character: GameObject, location: GameObject) -> float:
        """Scores a location using location preference rules.

        Parameters
        ----------
        character
            The character to calculate scores for
        location
            The location to score

        Returns
        -------
        float
            The probability of wanting to frequent this location
        """

        cumulative_score: float = 1.0
        consideration_count: int = 0
        rule_library = character.world.resource_manager.get_resource(
            LocationPreferenceRuleLibrary
        )

        for rule_info in rule_library.iter_rules():
            consideration_score = rule_info.rule(character, location)
            if consideration_score is not None:
                assert 0.0 <= consideration_score
                cumulative_score *= consideration_score
                consideration_count += 1

            if cumulative_score == 0.0:
                break

        if consideration_count == 0:
            consideration_count = 1
            cumulative_score = 0.0

        # Scores are averaged using the Geometric Mean instead of
        # arithmetic mean. It calculates the mean of a product of
        # n-numbers by finding the n-th root of the product
        # Tried using the averaging scheme by Dave Mark, but it
        # returned values that felt too small and were not easy
        # to reason about.
        # Using this method, a cumulative score of zero will still
        # result in a final score of zero.

        final_score = cumulative_score ** (1 / consideration_count)

        return final_score

    @staticmethod
    def calculate_location_probabilities(
        character: GameObject, locations: List[GameObject]
    ) -> List[Tuple[float, GameObject]]:
        """Calculate probability distribution for a character and set of locations."""

        score_total: float = 0
        scores: List[Tuple[float, GameObject]] = []

        # Score each location
        for loc in locations:
            score = UpdateFrequentedLocationSystem.score_location(character, loc)
            score_total += math.exp(score)
            scores.append((math.exp(score), loc))

        # Perform softmax
        probabilities = [(score / score_total, loc) for score, loc in scores]

        # Sort
        probabilities.sort(key=lambda pair: pair[0], reverse=True)

        return probabilities

    @staticmethod
    def score_locations(
        character: GameObject,
    ) -> List[Tuple[float, GameObject]]:
        """Score potential locations for the character to frequent.

        Parameters
        ----------
        character
            The character to score the location in reference to

        Returns
        -------
        List[Tuple[float, GameObject]]
            A list of tuples containing location scores and the location, sorted in
            descending order
        """

        locations = [
            character.world.gameobject_manager.get_gameobject(guid)
            for guid, (_, _, _) in character.world.get_components(
                (Location, Services, Active)
            )
        ]

        scores = UpdateFrequentedLocationSystem.calculate_location_probabilities(
            character, locations
        )

        return scores

    def on_update(self, world: World) -> None:
        # Frequented locations are sampled from the current settlement
        # that the character belongs to
        for guid, (
            frequented_locations,
            life_stage,
            _,
        ) in world.get_components((FrequentedLocations, LifeStage, Active)):
            if life_stage.life_stage < LifeStageType.YoungAdult:
                continue

            character = world.gameobject_manager.get_gameobject(guid)

            if len(frequented_locations) < self.ideal_location_count:
                # Try to find additional places to frequent
                places_to_find = max(
                    0, self.ideal_location_count - len(frequented_locations)
                )

                location_scores = UpdateFrequentedLocationSystem.score_locations(
                    character
                )

                for score, location in location_scores:
                    if (
                        score > self.location_score_threshold
                        and location not in frequented_locations
                    ):
                        character.get_component(FrequentedLocations).add_location(
                            location
                        )
                        places_to_find -= 1

                    if places_to_find == 0:
                        break


class AIActionSystem(System):
    """AIs execute actions.

    This system loops through all the AIComponents and has them attempt to execute
    actions that have been suggested to them by other systems. This system should run
    later in the update phase to allow other systems to suggest actions, but it should
    run before the late-update phase to allow event listeners to respond to events
    generated by actions.
    """

    __slots__ = "goal_utility_threshold"

    goal_utility_threshold: float

    def __init__(self, goal_utility_threshold: float = 0.3) -> None:
        super().__init__()
        self.goal_utility_threshold = goal_utility_threshold

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)
        for guid, (_, goals, _) in world.get_components((AIBrain, Goals, Active)):
            gameobject = world.gameobject_manager.get_gameobject(guid)
            # GameObjects may have become deactivated by the actions of
            # another that ran before them in this loop. We need to ensure
            # that inactive GameObjects are not pursuing goals
            if gameobject.has_component(Active) is False:
                continue

            if not goals.has_options():
                goals.clear_goals()
                continue

            goal = goals.pick_one(rng)

            if (
                not goal.is_complete()
                and goal.get_utility()[gameobject] >= self.goal_utility_threshold
            ):
                goal.take_action()

            goals.clear_goals()


class DeathSystem(System):
    """Characters die when their health hits zero."""

    def on_update(self, world: World) -> None:
        for _, (_, _, health) in world.get_components((Active, GameCharacter, Health)):
            if health.value <= 0:
                die(health.gameobject)


class GoOutOfBusinessSystem(System):
    @staticmethod
    def calculate_probability_of_closing(business: GameObject) -> float:
        """Calculate the probability of a business randomly going out of business."""
        lifespan = business.get_component(Lifespan).value
        current_date = business.world.resource_manager.get_resource(SimDateTime)

        years_in_business: int = (
            current_date.year - business.get_component(OpenForBusiness).timestamp
        )

        return (years_in_business / (lifespan + 10)) ** 2

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)
        for guid, _ in world.get_components((Business, OpenForBusiness, Active)):
            business = world.gameobject_manager.get_gameobject(guid)
            probability_of_closing = (
                GoOutOfBusinessSystem.calculate_probability_of_closing(business)
            )
            if rng.random() < probability_of_closing:
                shutdown_business(business)


class PregnancySystem(System):
    """Some characters may get pregnant when in romantic relationships."""

    @staticmethod
    def get_probability_of_pregnancy(
        parent_a: GameObject, parent_b: GameObject
    ) -> float:
        """Calculate probability of a character getting pregnant."""
        parent_a_fertility = parent_a.get_component(Fertility).value
        parent_b_fertility = parent_b.get_component(Fertility).value

        if parent_a_fertility == 0.0 or parent_b_fertility == 0.0:
            return 0.0

        return (parent_a_fertility + parent_b_fertility) / 2.0

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)
        date = world.resource_manager.get_resource(SimDateTime)

        for guid, _ in world.get_components((CanGetPregnant, Active)):
            character = world.gameobject_manager.get_gameobject(guid)

            if not character.has_component(Pregnant):
                continue

            potential_partners: List[GameObject] = []

            # Try to find a romantic partner
            for other_character, relationship in character.get_component(
                Relationships
            ).outgoing.items():
                if not other_character.has_component(Active):
                    continue

                if not other_character.has_component(CanGetOthersPregnant):
                    continue

                if not (
                    relationship.has_component(Dating)
                    or relationship.has_component(Married)
                ):
                    continue

                potential_partners.append(other_character)

            if potential_partners:
                chosen_partner = rng.choice(potential_partners)

                if rng.random() < PregnancySystem.get_probability_of_pregnancy(
                    character, chosen_partner
                ):
                    character.add_component(
                        Pregnant,
                        partner=chosen_partner,
                        year_created=date.year,
                    )

                    event = GetPregnantEvent(world, date, character, chosen_partner)

                    event.dispatch()


class DatingBreakUpSystem(System):
    def on_update(self, world: World) -> None:
        for _, (relationship, _, _) in world.get_components(
            (Relationship, Dating, Active)
        ):
            owner = relationship.owner
            target = relationship.target
            goal = BreakUp(owner, target)
            utility = goal.get_utility().get(owner, 0)
            if utility > 0:
                owner.get_component(Goals).push_goal(utility, goal)


class MarriageSystem(System):
    def on_update(self, world: World) -> None:
        for _, (relationship, _, _) in world.get_components(
            (Relationship, Dating, Active)
        ):
            owner = relationship.owner
            target = relationship.target
            goal = GetMarried(owner, target)
            utility = goal.get_utility().get(owner, 0)
            if utility > 0:
                owner.get_component(Goals).push_goal(utility, goal)


class EndMarriageSystem(System):
    def on_update(self, world: World) -> None:
        for _, (relationship, _, _) in world.get_components(
            (Relationship, Married, Active)
        ):
            owner = relationship.owner
            target = relationship.target
            goal = GetDivorced(owner, target)
            utility = goal.get_utility().get(owner, 0)
            if utility > 0:
                owner.get_component(Goals).push_goal(utility, goal)


class FindRomanceSystem(System):
    """
    Handles the dating/breakup loop

    This system is responsible for supplying characters with the goal to start dating or
    the goal to break up if they are already in a romantic relationship.
    """

    def on_update(self, world: World) -> None:
        for guid, (goals, _, life_stage) in world.get_components(
            (Goals, Active, LifeStage)
        ):
            character = world.gameobject_manager.get_gameobject(guid)
            if (
                is_single(character)
                and life_stage.life_stage >= LifeStageType.Adolescent
            ):
                goal = FindRomance(character)
                utility = goal.get_utility().get(character, 0)
                if utility > 0:
                    goals.push_goal(utility, goal)


class FindOwnPlaceSystem(System):
    """
    This system looks for young-adult to adult-aged characters who don't own their own
    residence and encourages them to find their own residence or leave the simulation
    """

    def on_update(self, world: World) -> None:
        for guid, (_, _, life_stage, resident, goals) in world.get_components(
            (GameCharacter, Active, LifeStage, Resident, Goals)
        ):
            if (
                life_stage.life_stage == LifeStageType.Adult
                or life_stage.life_stage == LifeStageType.YoungAdult
            ):
                residence = resident.residence.get_component(Residence)
                character = world.gameobject_manager.get_gameobject(guid)
                if not residence.is_owner(character):
                    goal = FindOwnPlace(character)
                    utility = goal.get_utility()[character]
                    goals.push_goal(utility, goal)


class RetirementSystem(System):
    """Encourages senior residents to retire from all their jobs."""

    def on_update(self, world: World) -> None:
        for guid, (_, _, life_stage, roles, goals) in world.get_components(
            (GameCharacter, Active, LifeStage, Roles, Goals)
        ):
            if life_stage.life_stage == LifeStageType.Senior and len(
                roles.get_roles_of_type(Occupation)
            ):
                character = world.gameobject_manager.get_gameobject(guid)
                goal = Retire(character)
                utility = goal.get_utility()[character]
                goals.push_goal(utility, goal)
