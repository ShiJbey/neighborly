from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Type, cast

from neighborly.ai.behavior_tree import (
    AbstractBTNode,
    BehaviorTree,
    NodeState,
    SelectorBTNode,
)
from neighborly.ai.brain import (
    Consideration,
    ConsiderationDict,
    ConsiderationList,
    GoalNode,
    WeightedList,
)
from neighborly.components.business import (
    Business,
    BusinessOwner,
    BusinessType,
    Occupation,
    OpenForBusiness,
    RetirementEvent,
    StartBusinessEvent,
    Unemployed,
)
from neighborly.components.character import (
    Dating,
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
from neighborly.components.residence import (
    Residence,
    ResidenceType,
    Resident,
    Vacant,
    set_residence,
)
from neighborly.config import NeighborlyConfig
from neighborly.ecs import Active, GameObject, World
from neighborly.events import (
    BreakUpEvent,
    DivorceEvent,
    MarriageEvent,
    StartDatingEvent,
)
from neighborly.life_event import EventRole, EventRoleList
from neighborly.relationship import (
    Friendship,
    Relationships,
    Romance,
    get_relationship,
    get_relationships_with_components,
    has_relationship,
)
from neighborly.roles import Roles
from neighborly.spawn_table import BusinessSpawnTable, ResidenceSpawnTable
from neighborly.time import SimDateTime
from neighborly.utils.common import (
    depart_settlement,
    die,
    end_job,
    shutdown_business,
    start_job,
)
from neighborly.utils.query import are_related, is_single
from neighborly.world_map import BuildingMap

####################################
# CONSIDERATIONS
####################################


def employment_spouse_consideration(gameobject: GameObject) -> Optional[float]:
    if (
        len(
            gameobject.get_component(Relationships).get_relationships_with_components(
                Married
            )
        )
        > 0
    ):
        return 0.7


def employment_children_consideration(gameobject: GameObject) -> Optional[float]:
    child_count = float(
        len(
            gameobject.get_component(Relationships).get_relationships_with_components(
                ParentOf
            )
        )
    )
    if child_count:
        return min(1.0, child_count / 5.0)


def has_occupation_consideration(gameobject: GameObject) -> Optional[float]:
    if roles := gameobject.try_component(Roles):
        if len(roles.get_roles_of_type(Occupation)):
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
        current_year = gameobject.world.resource_manager.get_resource(SimDateTime).year
        years_unemployed = current_year - unemployed.timestamp
        return min(1.0, float(years_unemployed) / 6.0)


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
        self.roles = EventRoleList([EventRole("Character", character)])

    @property
    def character(self):
        return self.roles["Character"]

    def is_complete(self) -> bool:
        return bool(self.character.get_component(Roles).get_roles_of_type(Occupation))

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
        building_map = world.resource_manager.get_resource(BuildingMap)
        rng = world.resource_manager.get_resource(random.Random)

        # Get all the eligible business prefabs that are eligible for building
        # and the character meets the requirements for the owner occupation
        business_type = StartBusiness._get_business_character_can_own(self.character)

        if business_type is None:
            return NodeState.FAILURE

        vacancies = building_map.get_vacant_lots()

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return NodeState.FAILURE

        # Pick a random lot from those available
        lot = rng.choice(vacancies)

        # Instantiate the new business
        business = business_type.instantiate(world=world, lot=lot)

        # Emit the event first before emitting the event from
        # starting the new job
        StartBusinessEvent(
            world,
            world.resource_manager.get_resource(SimDateTime),
            self.character,
            business,
            business.get_component(Business).owner_type,
        ).dispatch()

        start_job(
            self.character,
            business,
            business.get_component(Business).owner_type,
            is_owner=True,
        )

        return NodeState.SUCCESS

    @staticmethod
    def _get_business_character_can_own(
        character: GameObject,
    ) -> Optional[Type[BusinessType]]:
        """Search the BusinessLibrary for BusinessTypes the character is can own."""

        world = character.world
        business_spawn_table = world.resource_manager.get_resource(BusinessSpawnTable)
        rng = world.resource_manager.get_resource(random.Random)

        choices: List[Type[BusinessType]] = []
        weights: List[int] = []

        for business_type_name in business_spawn_table.get_eligible(world):
            business_type = cast(
                Type[BusinessType], world.resolve_component_type(business_type_name)
            )

            owner_type: Type[Occupation] = business_type.config.owner_type

            if owner_type.job_requirements.passes_requirements(character):
                choices.append(business_type)
                weights.append(business_spawn_table.get_frequency(business_type_name))

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
        if roles := self.character.try_component(Roles):
            return bool(roles.get_roles_of_type(Occupation))
        return False

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

            for occupation_type in open_positions:
                if occupation_type.job_requirements.passes_requirements(self.character):
                    start_job(
                        self.character,
                        self.world.gameobject_manager.get_gameobject(guid),
                        occupation_type,
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
            residence = resident.residence.get_component(Residence)
            return residence.is_owner(self.character)
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
            residence_obj = self.world.gameobject_manager.get_gameobject(guid)
            set_residence(self.character, residence_obj, True)
            return NodeState.SUCCESS

        # self.blackboard["reason_to_depart"] = "No housing"
        return NodeState.FAILURE


class BuildNewHouse(AbstractBTNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character

    def evaluate(self) -> NodeState:
        world = self.character.world

        building_map = world.resource_manager.get_resource(BuildingMap)
        vacancies = building_map.get_vacant_lots()
        spawn_table = world.resource_manager.get_resource(ResidenceSpawnTable)
        rng = world.resource_manager.get_resource(random.Random)

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            # self.blackboard["reason_to_depart"] = "No housing"
            return NodeState.FAILURE

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(building_map.get_total_lots()) < 0.4:
            # self.blackboard["reason_to_depart"] = "No housing"
            return NodeState.FAILURE

        # Pick a random lot from those available
        lot = rng.choice(vacancies)

        residence_type_name: str = spawn_table.choose_random(rng)

        residence_type = cast(
            Type[ResidenceType], world.resolve_component_type(residence_type_name)
        )

        residence = residence_type.instantiate(world, lot=lot)

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
        depart_settlement(self.character, self.blackboard.get("reason_to_depart", None))
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
        initiator_to_target_romance = float(
            self.character.get_component(Relationships)
            .outgoing[self.partner]
            .get_component(Romance)
            .value
        )

        target_to_initiator_romance = float(
            self.partner.get_component(Relationships)
            .outgoing[self.character]
            .get_component(Romance)
            .value
        )

        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        lambda gameobject: (
                            (initiator_to_target_romance + 100.0) / 200.0
                        ),
                        lambda gameobject: 0.75 if is_single(gameobject) else 0.05,
                        virtue_consideration(Virtue.ROMANCE),
                    ]
                ),
                self.partner: ConsiderationList(
                    [
                        lambda gameobject: (
                            (target_to_initiator_romance + 100.0) / 200.0
                        ),
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
        rng = world.resource_manager.get_resource(random.Random)
        current_date = world.resource_manager.get_resource(SimDateTime)

        rel_to_initiator = get_relationship(self.partner, self.character)

        romance = rel_to_initiator.get_component(Romance)

        if rng.random() > ((romance.value + 100.0) / 200.0) ** 2:
            return NodeState.FAILURE

        get_relationship(self.character, self.partner).remove_component(Dating)
        get_relationship(self.partner, self.character).remove_component(Dating)
        get_relationship(self.character, self.partner).add_component(
            Married, timestamp=current_date.year
        )
        get_relationship(self.partner, self.character).add_component(
            Married, timestamp=current_date.year
        )

        event = MarriageEvent(
            world,
            self.character.world.resource_manager.get_resource(SimDateTime),
            self.character,
            self.partner,
        )

        world.event_manager.dispatch_event(event)

        return NodeState.SUCCESS

    def satisfied_goals(self) -> List[GoalNode]:
        return [
            FindRomance(self.character),
            FindRomance(self.partner),
            GetMarried(self.partner, self.character),
        ]

    def is_complete(self) -> bool:
        return get_relationship(self.character, self.partner).has_component(Married)

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
        return not get_relationship(self.character, self.partner).has_component(Dating)

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
                current_date = world.resource_manager.get_resource(SimDateTime)
                rel = get_relationship(gameobject, partner)
                dating_status = rel.get_component(Dating)
                years_together = current_date.year - dating_status.timestamp
                return min(1.0, years_together / 5.0)

            return 0.0

        return consideration

    def get_utility(self) -> Dict[GameObject, float]:
        character_to_partner = (
            get_relationship(self.character, self.partner).get_component(Romance).value
        )
        partner_to_character = (
            get_relationship(self.partner, self.character).get_component(Romance).value
        )

        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        invert_consideration(
                            lambda gameobject: (
                                ((character_to_partner + 100.0) / 200.0) ** 2
                            )
                        ),
                        invert_consideration(virtue_consideration(Virtue.ROMANCE)),
                        self.time_together_consideration(self.partner),
                    ]
                ),
                self.partner: ConsiderationList(
                    [
                        invert_consideration(
                            lambda gameobject: (
                                ((partner_to_character + 100.0) / 200.0) ** 2
                            )
                        ),
                        invert_consideration(virtue_consideration(Virtue.ROMANCE)),
                        self.time_together_consideration(self.character),
                    ]
                ),
            }
        ).calculate_scores()

    def evaluate(self) -> NodeState:
        get_relationship(self.character, self.partner).remove_component(Dating)
        get_relationship(self.partner, self.character).remove_component(Dating)

        get_relationship(self.character, self.partner).get_component(
            Romance
        ).base_value += -6
        get_relationship(self.partner, self.character).get_component(
            Romance
        ).base_value += -6

        get_relationship(self.character, self.partner).get_component(
            Friendship
        ).base_value += -6
        get_relationship(self.partner, self.character).get_component(
            Friendship
        ).base_value += -6

        event = BreakUpEvent(
            self.character.world,
            self.character.world.resource_manager.get_resource(SimDateTime),
            self.character,
            self.partner,
        )

        self.character.world.event_manager.dispatch_event(event)

        return NodeState.SUCCESS


class GetDivorced(GoalNode):
    __slots__ = "character", "partner"

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.partner: GameObject = partner

    def is_complete(self) -> bool:
        return not get_relationship(self.character, self.partner).has_component(Married)

    @staticmethod
    def time_together_consideration(partner: GameObject):
        def consideration(gameobject: GameObject) -> Optional[float]:
            if has_relationship(gameobject, partner):
                world = gameobject.world
                current_date = world.resource_manager.get_resource(SimDateTime)
                rel = get_relationship(gameobject, partner)
                married_status = rel.get_component(Married)
                year_together = current_date.year - married_status.timestamp
                return max(0.3, year_together / 10.0)

            return 0.0

        return consideration

    def get_utility(self) -> Dict[GameObject, float]:
        character_to_partner = (
            get_relationship(self.character, self.partner).get_component(Romance).value
        )
        partner_to_character = (
            get_relationship(self.partner, self.character).get_component(Romance).value
        )

        return ConsiderationDict(
            {
                self.character: ConsiderationList(
                    [
                        invert_consideration(
                            lambda gameobject: (
                                ((character_to_partner + 100.0) / 200.0) ** 2
                            )
                        ),
                        invert_consideration(virtue_consideration(Virtue.ROMANCE)),
                        self.time_together_consideration(self.partner),
                    ]
                ),
                self.partner: ConsiderationList(
                    [
                        invert_consideration(
                            lambda gameobject: (
                                ((partner_to_character + 100.0) / 200.0) ** 2
                            )
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
        get_relationship(self.character, self.partner).remove_component(Married)
        get_relationship(self.partner, self.character).remove_component(Married)

        get_relationship(self.character, self.partner).get_component(
            Romance
        ).base_value += -10
        get_relationship(self.partner, self.character).get_component(
            Romance
        ).base_value += -10

        get_relationship(self.character, self.partner).get_component(
            Friendship
        ).base_value += -10
        get_relationship(self.partner, self.character).get_component(
            Friendship
        ).base_value += -10

        event = DivorceEvent(
            self.character.world,
            self.character.world.resource_manager.get_resource(SimDateTime),
            self.character,
            self.partner,
        )

        self.character.world.event_manager.dispatch_event(event)

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
        return self.character.has_component(Retired)

    @staticmethod
    def life_stage_consideration(gameobject: GameObject) -> Optional[float]:
        if life_stage := gameobject.try_component(LifeStage):
            if life_stage.life_stage < LifeStageType.Senior:
                return 0.01
            else:
                return 0.85

    def get_utility(self) -> Dict[GameObject, float]:
        return ConsiderationDict(
            {self.character: ConsiderationList([self.life_stage_consideration])}
        ).calculate_scores()

    def evaluate(self) -> NodeState:
        world = self.character.world
        current_date = world.resource_manager.get_resource(SimDateTime)
        self.character.add_component(Retired, timestamp=current_date.year)

        for occupation in self.character.get_component(Roles).get_roles_of_type(
            Occupation
        ):
            event = RetirementEvent(
                world,
                world.resource_manager.get_resource(SimDateTime),
                self.character,
                occupation.business,
                type(occupation),
            )

            self.character.world.event_manager.dispatch_event(event)

            if business_owner := self.character.try_component(BusinessOwner):
                shutdown_business(business_owner.business)
            else:
                end_job(
                    character=self.character, business=occupation.business, reason=event
                )

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
        rng = world.resource_manager.get_resource(random.Random)
        current_date = world.resource_manager.get_resource(SimDateTime)

        rel_to_initiator = get_relationship(self.target, self.initiator)

        romance = rel_to_initiator.get_component(Romance)

        if rng.random() > ((romance.value + 100.0) / 200.0) ** 2:
            return NodeState.FAILURE

        get_relationship(self.initiator, self.target).add_component(
            Dating, timestamp=current_date.year
        )
        get_relationship(self.target, self.initiator).add_component(
            Dating, timestamp=current_date.year
        )

        event = StartDatingEvent(
            self.initiator.world,
            self.initiator.world.resource_manager.get_resource(SimDateTime),
            self.initiator,
            self.target,
        )

        self.target.world.event_manager.dispatch_event(event)

        return NodeState.SUCCESS

    def get_utility(self) -> Dict[GameObject, float]:
        initiator_to_target_romance = float(
            self.initiator.get_component(Relationships)
            .outgoing[self.target]
            .get_component(Romance)
            .value
        )

        target_to_initiator_romance = float(
            self.target.get_component(Relationships)
            .outgoing[self.initiator]
            .get_component(Romance)
            .value
        )

        return ConsiderationDict(
            {
                self.initiator: ConsiderationList(
                    [
                        lambda gameobject: (
                            (initiator_to_target_romance + 100.0) / 200.0
                        ),
                        lambda gameobject: 0.75 if is_single(gameobject) else 0.05,
                        virtue_consideration(Virtue.ROMANCE),
                    ]
                ),
                self.target: ConsiderationList(
                    [
                        lambda gameobject: (
                            (target_to_initiator_romance + 100.0) / 200.0
                        ),
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
        is_dating = len(get_relationships_with_components(self.character, Dating)) > 0
        is_married = len(get_relationships_with_components(self.character, Married)) > 0
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

        romance_threshold = world.resource_manager.get_resource(
            NeighborlyConfig
        ).settings.get("dating_romance_threshold", 25)

        # This character should try asking out another character
        candidates = [c for c in self.character.get_component(Relationships).outgoing]

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

            if outgoing_romance.value < romance_threshold:
                continue

            if are_related(self.character, other):
                continue

            if other == self.character:
                continue

            actions.append(outgoing_romance.value, AskOut(self.character, other))

        if actions:
            chosen = actions.pick_one(
                world.resource_manager.get_resource(random.Random)
            )
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
        die(self.character)
        return NodeState.SUCCESS
