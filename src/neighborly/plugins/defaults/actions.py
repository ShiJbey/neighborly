from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from neighborly.components import CurrentSettlement, Residence, Resident, Vacant
from neighborly.components.business import (
    Business,
    BusinessOwner,
    Occupation,
    OccupationTypes,
    OpenForBusiness,
    Unemployed,
)
from neighborly.components.character import (
    Dating,
    Deceased,
    Departed,
    GameCharacter,
    LifeStage,
    LifeStageType,
    Married,
    ParentOf,
    Retired,
    Virtue,
    Virtues,
)
from neighborly.components.spawn_table import BusinessSpawnTable, ResidenceSpawnTable
from neighborly.config import NeighborlyConfig
from neighborly.core.ai.behavior_tree import (
    AbstractBTNode,
    BehaviorTree,
    NodeState,
    SelectorBTNode,
)
from neighborly.core.ai.brain import (
    Consideration,
    ConsiderationDict,
    ConsiderationList,
    GoalNode,
    WeightedList,
)
from neighborly.core.ecs import (
    Active,
    EntityPrefab,
    GameObject,
    GameObjectFactory,
    World,
)
from neighborly.core.life_event import AllEvents
from neighborly.core.relationship import (
    Friendship,
    RelationshipManager,
    Romance,
    add_relationship_status,
    get_relationship,
    get_relationships_with_statuses,
    has_relationship,
    has_relationship_status,
    remove_relationship_status,
)
from neighborly.core.roles import Role, RoleList
from neighborly.core.settlement import Settlement
from neighborly.core.status import add_status, clear_statuses
from neighborly.core.time import DAYS_PER_MONTH, DAYS_PER_YEAR, SimDateTime
from neighborly.events import (
    BreakUpEvent,
    DeathEvent,
    DivorceEvent,
    MarriageEvent,
    RetirementEvent,
    StartBusinessEvent,
    StartDatingEvent,
)
from neighborly.utils.common import (
    add_business_to_settlement,
    add_residence_to_settlement,
    clear_frequented_locations,
    depart_settlement,
    end_job,
    remove_character_from_settlement,
    set_residence,
    shutdown_business,
    spawn_business,
    spawn_residence,
    start_job,
)
from neighborly.utils.query import are_related, get_work_experience_as, is_single

####################################
# CONSIDERATIONS
####################################


def employment_spouse_consideration(gameobject: GameObject) -> Optional[float]:
    if len(get_relationships_with_statuses(gameobject, Married)) > 0:
        return 0.7


def employment_children_consideration(gameobject: GameObject) -> Optional[float]:
    child_count = float(len(get_relationships_with_statuses(gameobject, ParentOf)))
    if child_count:
        return min(1.0, child_count / 5.0)


def has_occupation_consideration(gameobject: GameObject) -> Optional[float]:
    if gameobject.has_component(Occupation):
        return 0.0


def virtue_consideration(virtue: Virtue):
    def consideration(gameobject: GameObject) -> Optional[float]:
        if virtues := gameobject.try_component(Virtues):
            return (virtues[virtue] + 50.0) / 100.0

    return consideration


def ambition_consideration(gameobject: GameObject) -> Optional[float]:
    if virtues := gameobject.try_component(Virtues):
        return (virtues[Virtue.AMBITION] + 50.0) / 100.0


def reliability_consideration(gameobject: GameObject) -> Optional[float]:
    if virtues := gameobject.try_component(Virtues):
        return (virtues[Virtue.RELIABILITY] + 50.0) / 100.0


def independence_consideration(gameobject: GameObject) -> Optional[float]:
    if virtues := gameobject.try_component(Virtues):
        return (virtues[Virtue.INDEPENDENCE] + 50.0) / 100.0


def time_unemployed_consideration(gameobject: GameObject) -> Optional[float]:
    if unemployed := gameobject.get_component(Unemployed):
        months_unemployed = (
            gameobject.world.get_resource(SimDateTime) - unemployed.created
        ).total_days / DAYS_PER_MONTH

        return min(1.0, float(months_unemployed) / 6.0)


def employment_life_stage_consideration(gameobject: GameObject) -> Optional[float]:
    if life_stage := gameobject.try_component(LifeStage):
        if life_stage.life_stage == LifeStageType.Child:
            return 0.0
        elif life_stage.life_stage == LifeStageType.Adolescent:
            return 0.0
        elif life_stage.life_stage == LifeStageType.YoungAdult:
            return 0.6
        elif life_stage.life_stage == LifeStageType.Adult:
            return 0.8
        elif life_stage.life_stage == LifeStageType.Senior:
            return 0.05


def invert_consideration(c: Consideration):
    def consideration(gameobject: GameObject) -> Optional[float]:
        consideration_score = c(gameobject)
        if consideration_score is None:
            return None
        return 1.0 - consideration_score

    return consideration


class FindEmployment(GoalNode):
    considerations: Dict[str, ConsiderationList] = {
        "Character": ConsiderationList(
            [
                employment_children_consideration,
                employment_spouse_consideration,
                has_occupation_consideration,
                ambition_consideration,
                reliability_consideration,
                independence_consideration,
                time_unemployed_consideration,
                employment_life_stage_consideration,
            ]
        )
    }

    __slots__ = "roles"

    def __init__(self, character: GameObject) -> None:
        super().__init__(SelectorBTNode([GetJob(character), StartBusiness(character)]))
        self.roles = RoleList([Role("Character", character)])

    @property
    def character(self):
        return self.roles["Character"]

    def is_complete(self) -> bool:
        return self.character.has_component(Occupation)

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, FindEmployment):
            return self.character == __o.character
        return False

    def get_utility(self) -> Dict[GameObject, float]:
        """
        Calculate how important and beneficial this goal is

        Returns
        -------
        Dict[GameObject, float]
            GameObjects mapped to the utility they derive from the goal
        """
        utilities: Dict[GameObject, float] = {}

        for role in self.roles:
            utilities[role.gameobject] = self.considerations[role.name].calculate_score(
                role.gameobject
            )

        return utilities

    @classmethod
    def add_consideration(cls, role: str, consideration: Consideration) -> None:
        cls.considerations[role].append(consideration)


class StartBusiness(GoalNode):
    __slots__ = "character", "world"

    def __init__(self, character: GameObject):
        super().__init__()
        self.character = character
        self.world = character.world

    def is_complete(self) -> bool:
        return self.character.has_component(BusinessOwner)

    def satisfied_goals(self) -> List[GoalNode]:
        return [FindEmployment(self.character)]

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, StartBusiness):
            return self.character == __o.character
        return False

    def get_utility(self) -> Dict[GameObject, float]:
        """
        Calculate how important and beneficial this goal is

        Returns
        -------
        Dict[GameObject, float]
            GameObjects mapped to the utility they derive from the goal
        """
        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        employment_children_consideration,
                        employment_spouse_consideration,
                        has_occupation_consideration,
                        ambition_consideration,
                        reliability_consideration,
                        independence_consideration,
                        time_unemployed_consideration,
                        employment_life_stage_consideration,
                    ]
                )
            }
        ).calculate_scores()

    def evaluate(self) -> NodeState:
        world = self.character.world
        current_settlement = self.character.get_component(CurrentSettlement)
        settlement = world.get_gameobject(current_settlement.settlement)
        settlement_comp = settlement.get_component(Settlement)
        rng = world.get_resource(random.Random)

        # Get all the eligible business prefabs that are eligible for building
        # and the character meets the requirements for the owner occupation
        business_prefab = self._get_business_character_can_own(self.character)

        if business_prefab is None:
            return NodeState.FAILURE

        vacancies = settlement_comp.land_map.get_vacant_lots()

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return NodeState.FAILURE

        # Pick a random lot from those available
        lot = rng.choice(vacancies)

        owner_type = business_prefab.components["Business"]["owner_type"]

        assert owner_type

        owner_occupation_type = OccupationTypes.get(owner_type)

        business = spawn_business(world, business_prefab.name)

        add_business_to_settlement(
            business,
            world.get_gameobject(settlement.uid),
            lot_id=lot,
        )

        start_business_event = StartBusinessEvent(
            world.get_resource(SimDateTime),
            self.character,
            business,
            owner_occupation_type.name,
        )

        self.character.fire_event(start_business_event)

        world.get_resource(AllEvents).append(start_business_event)

        start_job(self.character, business, owner_occupation_type.name, is_owner=True)

        return NodeState.SUCCESS

    @staticmethod
    def _get_business_character_can_own(
        character: GameObject,
    ) -> Optional[EntityPrefab]:
        world = character.world
        current_settlement = character.get_component(CurrentSettlement)
        settlement = world.get_gameobject(current_settlement.settlement)
        business_spawn_table = settlement.get_component(BusinessSpawnTable)
        rng = world.get_resource(random.Random)

        choices: List[EntityPrefab] = []
        weights: List[int] = []

        for prefab_name in business_spawn_table.get_eligible(settlement):
            prefab = GameObjectFactory.get(prefab_name)
            owner_type = prefab.components["Business"]["owner_type"]
            if owner_type:
                owner_occupation_type = OccupationTypes.get(owner_type)

                if owner_occupation_type.passes_preconditions(character):
                    choices.append(prefab)
                    weights.append(business_spawn_table.get_frequency(prefab_name))

        if choices:
            # Choose an archetype at random
            return rng.choices(choices, weights, k=1)[0]

        return None


class GetJob(GoalNode):
    """Defines a goal and behavior for a character getting a job"""

    __slots__ = "character", "world"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.world: World = character.world

    def get_utility(self) -> Dict[GameObject, float]:
        """
        Calculate how important and beneficial this goal is

        Returns
        -------
        Dict[GameObject, float]
            GameObjects mapped to the utility they derive from the goal
        """
        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        employment_children_consideration,
                        employment_spouse_consideration,
                        has_occupation_consideration,
                        ambition_consideration,
                        reliability_consideration,
                        independence_consideration,
                        time_unemployed_consideration,
                        employment_life_stage_consideration,
                    ]
                )
            }
        ).calculate_scores()

    def is_complete(self) -> bool:
        return self.character.has_component(Occupation)

    def satisfied_goals(self) -> List[GoalNode]:
        return [FindEmployment(self.character)]

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, GetJob):
            return self.character == __o.character
        return False

    def evaluate(self) -> NodeState:
        for guid, (business, _, _) in self.world.get_components(
            (Business, OpenForBusiness, Active)
        ):
            open_positions = business.get_open_positions()

            for occupation_name in open_positions:
                occupation_type = OccupationTypes.get(occupation_name)

                if occupation_type.passes_preconditions(self.character):
                    start_job(
                        self.character, self.world.get_gameobject(guid), occupation_name
                    )
                    return NodeState.SUCCESS

        return NodeState.FAILURE


class FindOwnPlace(GoalNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__(
            SelectorBTNode(
                [
                    FindVacantResidence(character),
                    BuildNewHouse(character),
                    DepartSimulation(character),
                ]
            )
        )
        self.character: GameObject = character

    def is_complete(self) -> bool:
        if resident := self.character.try_component(Resident):
            residence = self.character.world.get_gameobject(
                resident.residence
            ).get_component(Residence)
            return residence.is_owner(self.character.uid)
        return False

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    @staticmethod
    def life_stage_consideration(gameobject: GameObject) -> Optional[float]:
        if life_stage := gameobject.try_component(LifeStage):
            if life_stage.life_stage == LifeStageType.Adult:
                return 0.9

            elif life_stage.life_stage == LifeStageType.YoungAdult:
                return 0.5

            else:
                return 0

    def get_utility(self) -> Dict[GameObject, float]:
        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        self.life_stage_consideration,
                        virtue_consideration(Virtue.INDEPENDENCE),
                    ]
                )
            }
        ).calculate_scores()

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, FindOwnPlace):
            return self.character == __o.character
        return False


class FindVacantResidence(AbstractBTNode):
    __slots__ = "character", "world"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.world: World = character.world

    def evaluate(self) -> NodeState:
        for guid, _ in self.world.get_components((Residence, Active, Vacant)):
            residence_obj = self.world.get_gameobject(guid)
            set_residence(self.character, residence_obj, True)
            return NodeState.SUCCESS

        self.blackboard["reason_to_depart"] = "No housing"
        return NodeState.FAILURE


class BuildNewHouse(AbstractBTNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character

    def evaluate(self) -> NodeState:
        world = self.character.world

        settlement = world.get_gameobject(
            self.character.get_component(CurrentSettlement).settlement
        )
        land_map = settlement.get_component(Settlement).land_map
        vacancies = land_map.get_vacant_lots()
        spawn_table = settlement.get_component(ResidenceSpawnTable)
        rng = world.get_resource(random.Random)

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            self.blackboard["reason_to_depart"] = "No housing"
            return NodeState.FAILURE

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(land_map.get_total_lots()) < 0.4:
            self.blackboard["reason_to_depart"] = "No housing"
            return NodeState.FAILURE

        # Pick a random lot from those available
        lot = rng.choice(vacancies)

        prefab = spawn_table.choose_random(rng)

        residence = spawn_residence(world, prefab)

        add_residence_to_settlement(
            residence,
            settlement=world.get_gameobject(settlement.uid),
            lot_id=lot,
        )

        set_residence(self.character, residence, True)

        return NodeState.SUCCESS


class DepartSimulation(GoalNode):
    __slots__ = "character", "world"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.world: World = character.world

    def is_complete(self) -> bool:
        return self.character.has_component(Departed)

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def get_utility(self) -> Dict[GameObject, float]:
        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        time_unemployed_consideration,
                        FindOwnPlace.life_stage_consideration,
                    ]
                )
            }
        ).calculate_scores()

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, DepartSimulation):
            return self.character == __o.character
        return False

    def evaluate(self) -> NodeState:
        depart_settlement(self.character, self.blackboard.get("reason_to_depart", ""))
        return NodeState.SUCCESS


# class StartFamily(GoalNode):
#     __slots__ = "character"
#
#     def __init__(self, character: GameObject) -> None:
#         super().__init__(
#             SequenceBTNode([GetMarried(self.character), HaveChildren(self.character)])
#         )
#         self.character: GameObject = character
#
#     def is_complete(self) -> bool:
#         is_married = bool(get_relationships_with_statuses(self.character, Married))
#         has_children = bool(get_relationships_with_statuses(self.character, ParentOf))
#         return is_married and has_children
#
#     def satisfied_goals(self) -> List[GoalNode]:
#         return []
#
#     def get_utility(self) -> Dict[GameObject, float]:
#         return super().get_utility()
#
#     def __eq__(self, __o: object) -> bool:
#         if isinstance(__o, StartFamily):
#             return self.character == __o.character
#         return False
#
#
#
# class FindSignificantOther(GoalNode):
#     __slots__ = "character"
#
#     def __init__(self, character: GameObject) -> None:
#         super().__init__()
#         self.character: GameObject = character
#
#     def __eq__(self, __o: object) -> bool:
#         if isinstance(__o, FindSignificantOther):
#             return self.character == __o.character
#         return False
#
#
# class ProposeMarriage(GoalNode):
#     ...
#
#
# class HaveChildren(GoalNode):
#     __slots__ = "character"
#
#     def __init__(self, character: GameObject) -> None:
#         super().__init__()
#         self.character: GameObject = character
#
#     def __eq__(self, __o: object) -> bool:
#         if isinstance(__o, HaveChildren):
#             return self.character == __o.character
#         return False
#
#
# class GetPregnant(GoalNode):
#     __slots__ = "character"
#
#     def __init__(self, character: GameObject) -> None:
#         super().__init__()
#         self.character: GameObject = character
#
#     def __eq__(self, __o: object) -> bool:
#         if isinstance(__o, GetPregnant):
#             return self.character == __o.character
#         return False


class GetMarried(GoalNode):
    __slots__ = "character", "partner"

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.partner: GameObject = partner

    def get_utility(self) -> Dict[GameObject, float]:
        world = self.character.world

        initiator_to_target_romance = float(
            world.get_gameobject(
                self.character.get_component(RelationshipManager).outgoing[
                    self.partner.uid
                ]
            )
            .get_component(Romance)
            .get_value()
        )

        target_to_initiator_romance = float(
            world.get_gameobject(
                self.partner.get_component(RelationshipManager).outgoing[
                    self.character.uid
                ]
            )
            .get_component(Romance)
            .get_value()
        )

        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        lambda gameobject: (initiator_to_target_romance + 100.0)
                        / 200.0,
                        lambda gameobject: 0.75 if is_single(gameobject) else 0.05,
                        virtue_consideration(Virtue.ROMANCE),
                    ]
                ),
                self.partner: ConsiderationList(
                    [
                        lambda gameobject: (target_to_initiator_romance + 100.0)
                        / 200.0,
                        lambda gameobject: 0.75 if is_single(gameobject) else 0.05,
                        virtue_consideration(Virtue.ROMANCE),
                    ]
                ),
            }
        ).calculate_scores()

    def evaluate(self) -> NodeState:
        if not is_single(self.partner):
            return NodeState.FAILURE

        world = self.character.world
        rng = world.get_resource(random.Random)

        rel_to_initiator = get_relationship(self.partner, self.character)

        romance = rel_to_initiator.get_component(Romance)

        if rng.random() > ((romance.get_value() + 100.0) / 200.0) ** 2:
            return NodeState.FAILURE

        remove_relationship_status(self.character, self.partner, Dating)
        remove_relationship_status(self.partner, self.character, Dating)
        add_relationship_status(self.character, self.partner, Married())
        add_relationship_status(self.partner, self.character, Married())

        event = MarriageEvent(
            self.character.world.get_resource(SimDateTime),
            self.character,
            self.partner,
        )

        self.character.fire_event(event)
        self.partner.fire_event(event)

        self.character.world.get_resource(AllEvents).append(event)

        return NodeState.SUCCESS

    def satisfied_goals(self) -> List[GoalNode]:
        return [
            FindRomance(self.character),
            FindRomance(self.partner),
            GetMarried(self.partner, self.character),
        ]

    def is_complete(self) -> bool:
        return has_relationship_status(self.character, self.partner, Married)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, GetMarried):
            return self.character == __o.character and self.partner == __o.partner
        return False


class BreakUp(GoalNode):
    __slots__ = "character", "partner"

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.partner: GameObject = partner

    def is_complete(self) -> bool:
        return not has_relationship_status(self.character, self.partner, Dating)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, BreakUp):
            return self.character == __o.character and self.partner == __o.partner
        return False

    def satisfied_goals(self) -> List[GoalNode]:
        return [BreakUp(self.partner, self.character)]

    @staticmethod
    def time_together_consideration(partner: GameObject):
        def consideration(gameobject: GameObject) -> Optional[float]:
            if has_relationship(gameobject, partner):
                world = gameobject.world
                current_date = world.get_resource(SimDateTime)
                rel = get_relationship(gameobject, partner)
                dating_status = rel.get_component(Dating)
                time_together = (
                    float((current_date - dating_status.created).total_days)
                    / DAYS_PER_YEAR
                )
                return time_together / 5.0

            return 0.0

        return consideration

    def get_utility(self) -> Dict[GameObject, float]:
        character_to_partner = (
            get_relationship(self.character, self.partner)
            .get_component(Romance)
            .get_value()
        )
        partner_to_character = (
            get_relationship(self.partner, self.character)
            .get_component(Romance)
            .get_value()
        )

        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        invert_consideration(
                            lambda gameobject: ((character_to_partner + 100.0) / 200.0)
                            ** 2
                        ),
                        invert_consideration(virtue_consideration(Virtue.ROMANCE)),
                        self.time_together_consideration(self.partner),
                    ]
                ),
                self.partner: ConsiderationList(
                    [
                        invert_consideration(
                            lambda gameobject: ((partner_to_character + 100.0) / 200.0)
                            ** 2
                        ),
                        invert_consideration(virtue_consideration(Virtue.ROMANCE)),
                        self.time_together_consideration(self.character),
                    ]
                ),
            }
        ).calculate_scores()

    def evaluate(self) -> NodeState:
        remove_relationship_status(self.character, self.partner, Dating)
        remove_relationship_status(self.partner, self.character, Dating)

        get_relationship(self.character, self.partner).get_component(Romance).increment(
            -6
        )
        get_relationship(self.partner, self.character).get_component(Romance).increment(
            -6
        )

        get_relationship(self.character, self.partner).get_component(
            Friendship
        ).increment(-6)
        get_relationship(self.partner, self.character).get_component(
            Friendship
        ).increment(-6)

        event = BreakUpEvent(
            self.character.world.get_resource(SimDateTime),
            self.character,
            self.partner,
        )

        self.character.fire_event(event)
        self.partner.fire_event(event)

        self.character.world.get_resource(AllEvents).append(event)

        return NodeState.SUCCESS


class GetDivorced(GoalNode):
    __slots__ = "character", "partner"

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.partner: GameObject = partner

    def is_complete(self) -> bool:
        return not has_relationship_status(self.character, self.partner, Married)

    @staticmethod
    def time_together_consideration(partner: GameObject):
        def consideration(gameobject: GameObject) -> Optional[float]:
            if has_relationship(gameobject, partner):
                world = gameobject.world
                current_date = world.get_resource(SimDateTime)
                rel = get_relationship(gameobject, partner)
                married_status = rel.get_component(Married)
                time_together = (
                    float((current_date - married_status.created).total_days)
                    / DAYS_PER_YEAR
                )
                return max(0.3, time_together / 10.0)

            return 0.0

        return consideration

    def get_utility(self) -> Dict[GameObject, float]:
        character_to_partner = (
            get_relationship(self.character, self.partner)
            .get_component(Romance)
            .get_value()
        )
        partner_to_character = (
            get_relationship(self.partner, self.character)
            .get_component(Romance)
            .get_value()
        )

        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        invert_consideration(
                            lambda gameobject: ((character_to_partner + 100.0) / 200.0)
                            ** 2
                        ),
                        invert_consideration(virtue_consideration(Virtue.ROMANCE)),
                        self.time_together_consideration(self.partner),
                    ]
                ),
                self.partner: ConsiderationList(
                    [
                        invert_consideration(
                            lambda gameobject: ((partner_to_character + 100.0) / 200.0)
                            ** 2
                        ),
                        invert_consideration(virtue_consideration(Virtue.ROMANCE)),
                        self.time_together_consideration(self.character),
                    ]
                ),
            }
        ).calculate_scores()

    def satisfied_goals(self) -> List[GoalNode]:
        return [GetDivorced(self.partner, self.character)]

    def evaluate(self) -> NodeState:
        remove_relationship_status(self.character, self.partner, Married)
        remove_relationship_status(self.partner, self.character, Married)

        get_relationship(self.character, self.partner).get_component(Romance).increment(
            -10
        )
        get_relationship(self.partner, self.character).get_component(Romance).increment(
            -10
        )

        get_relationship(self.character, self.partner).get_component(
            Friendship
        ).increment(-10)
        get_relationship(self.partner, self.character).get_component(
            Friendship
        ).increment(-10)

        event = DivorceEvent(
            self.character.world.get_resource(SimDateTime),
            self.character,
            self.partner,
        )

        self.character.fire_event(event)
        self.partner.fire_event(event)

        self.character.world.get_resource(AllEvents).append(event)

        return NodeState.SUCCESS

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, GetDivorced):
            return self.character == __o.character and self.partner == __o.partner
        return False


class Retire(GoalNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character = character

    def is_complete(self) -> bool:
        is_retired = self.character.has_component(Retired)
        is_not_working = not self.character.has_component(Occupation)
        return is_retired or is_not_working

    @staticmethod
    def life_stage_consideration(gameobject: GameObject) -> Optional[float]:
        if life_stage := gameobject.try_component(LifeStage):
            if life_stage.life_stage < LifeStageType.Senior:
                return 0.01
            else:
                return 0.85

    @staticmethod
    def work_experience_consideration(gameobject: GameObject) -> Optional[float]:
        if occupation := gameobject.try_component(Occupation):
            # This is a nested function. So, we call it once to return the
            # precondition function, then we call it a second time
            experience = get_work_experience_as(occupation.occupation_type)(gameobject)

            return min(1.0, experience / 10.0)

    def get_utility(self) -> Dict[GameObject, float]:
        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [self.work_experience_consideration, self.life_stage_consideration]
                )
            }
        ).calculate_scores()

    def evaluate(self) -> NodeState:
        world = self.character.world
        add_status(self.character, Retired())

        occupation = self.character.get_component(Occupation)

        event = RetirementEvent(
            world.get_resource(SimDateTime),
            self.character,
            world.get_gameobject(occupation.business),
            occupation.occupation_type,
        )

        self.character.fire_event(event)

        world.get_resource(AllEvents).append(event)

        if business_owner := self.character.try_component(BusinessOwner):
            shutdown_business(world.get_gameobject(business_owner.business))
        else:
            end_job(self.character, "Retired")

        return NodeState.SUCCESS

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Retire):
            return self.character == __o.character
        return False


class AskOut(GoalNode):
    __slots__ = "initiator", "target"

    def __init__(self, initiator: GameObject, target: GameObject) -> None:
        super().__init__()
        self.initiator: GameObject = initiator
        self.target: GameObject = target

    def is_complete(self) -> bool:
        if not has_relationship(self.initiator, self.target):
            return False

        relationship = get_relationship(self.initiator, self.target)
        return relationship.has_component(Dating)

    def satisfied_goals(self) -> List[GoalNode]:
        return [FindRomance(self.initiator), FindRomance(self.target)]

    def evaluate(self) -> NodeState:
        if not is_single(self.target):
            return NodeState.FAILURE

        world = self.initiator.world
        rng = world.get_resource(random.Random)

        rel_to_initiator = get_relationship(self.target, self.initiator)

        romance = rel_to_initiator.get_component(Romance)

        if rng.random() > ((romance.get_value() + 100.0) / 200.0) ** 2:
            return NodeState.FAILURE

        add_relationship_status(self.initiator, self.target, Dating())
        add_relationship_status(self.target, self.initiator, Dating())

        event = StartDatingEvent(
            self.initiator.world.get_resource(SimDateTime),
            self.initiator,
            self.target,
        )

        self.initiator.fire_event(event)
        self.target.fire_event(event)
        self.initiator.world.get_resource(AllEvents).append(event)

        return NodeState.SUCCESS

    def get_utility(self) -> Dict[GameObject, float]:
        world = self.initiator.world

        initiator_to_target_romance = float(
            world.get_gameobject(
                self.initiator.get_component(RelationshipManager).outgoing[
                    self.target.uid
                ]
            )
            .get_component(Romance)
            .get_value()
        )

        target_to_initiator_romance = float(
            world.get_gameobject(
                self.target.get_component(RelationshipManager).outgoing[
                    self.initiator.uid
                ]
            )
            .get_component(Romance)
            .get_value()
        )

        return ConsiderationDict(
            {
                self.initiator: ConsiderationList(
                    [
                        lambda gameobject: (initiator_to_target_romance + 100.0)
                        / 200.0,
                        lambda gameobject: 0.75 if is_single(gameobject) else 0.05,
                        virtue_consideration(Virtue.ROMANCE),
                    ]
                ),
                self.target: ConsiderationList(
                    [
                        lambda gameobject: (target_to_initiator_romance + 100.0)
                        / 200.0,
                        lambda gameobject: 0.75 if is_single(gameobject) else 0.05,
                        virtue_consideration(Virtue.ROMANCE),
                    ]
                ),
            }
        ).calculate_scores()

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, AskOut):
            return self.initiator == __o.initiator and self.target == __o.target
        return False


class FindRomance(GoalNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character = character

    def is_complete(self) -> bool:
        is_dating = len(get_relationships_with_statuses(self.character, Dating)) > 0
        is_married = len(get_relationships_with_statuses(self.character, Married)) > 0
        return is_married or is_dating

    def get_utility(self) -> Dict[GameObject, float]:
        life_stage = self.character.get_component(LifeStage).life_stage
        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        virtue_consideration(Virtue.ROMANCE),
                        virtue_consideration(Virtue.LUST),
                        lambda gameobject: 1 if is_single(gameobject) else None,
                        lambda gameobject: (
                            0.8 if life_stage == LifeStageType.YoungAdult else None
                        ),
                        lambda gameobject: (
                            0.6 if life_stage == LifeStageType.Adult else None
                        ),
                        lambda gameobject: (
                            0.0 if life_stage == LifeStageType.Child else None
                        ),
                        lambda gameobject: (
                            0.3 if life_stage == LifeStageType.Senior else None
                        ),
                        lambda gameobject: (
                            0.7 if life_stage == LifeStageType.Adolescent else None
                        ),
                    ]
                )
            }
        ).calculate_scores()

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def evaluate(self) -> NodeState:
        """Perform an action in-service of this goal"""

        world = self.character.world

        romance_threshold = world.get_resource(NeighborlyConfig).settings.get(
            "dating_romance_threshold", 25
        )

        # This character should try asking out another character
        candidates = [
            world.get_gameobject(c)
            for c in self.character.get_component(RelationshipManager).outgoing
        ]

        actions: WeightedList[GoalNode] = WeightedList()

        for other in candidates:
            outgoing_relationship = get_relationship(self.character, other)

            outgoing_romance = outgoing_relationship.get_component(Romance)

            if not other.has_component(Active) or not other.has_component(
                GameCharacter
            ):
                continue

            if other.get_component(LifeStage).life_stage < LifeStageType.Adolescent:
                continue

            if not is_single(other):
                continue

            if outgoing_romance.get_value() < romance_threshold:
                continue

            if are_related(self.character, other):
                continue

            if other == self.character:
                continue

            actions.append(outgoing_romance.get_value(), AskOut(self.character, other))

        if actions:
            chosen = actions.pick_one(world.get_resource(random.Random))
            self.add_child(chosen)
            return chosen.evaluate()

        return NodeState.FAILURE

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__, "character": self.character.uid}

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, FindRomance):
            return self.character == __o.character
        return False


class Die(BehaviorTree):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character

    def evaluate(self) -> NodeState:
        event = DeathEvent(
            self.character.world.get_resource(SimDateTime), self.character
        )
        self.character.fire_event(event)
        self.character.world.get_resource(AllEvents).append(event)

        if self.character.has_component(Occupation):
            if business_owner := self.character.try_component(BusinessOwner):
                shutdown_business(
                    self.character.world.get_gameobject(business_owner.business)
                )
            else:
                end_job(self.character, reason="Died")

        if self.character.has_component(Resident):
            set_residence(self.character, None)

        add_status(self.character, Deceased())
        clear_frequented_locations(self.character)
        clear_statuses(self.character)

        remove_character_from_settlement(self.character)

        return NodeState.SUCCESS
