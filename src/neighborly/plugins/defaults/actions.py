from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from neighborly.components import CurrentSettlement, Residence, Vacant
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
from neighborly.core.ai.behavior_tree import NodeState, SelectorBTNode
from neighborly.core.ai.brain import GoalNode, WeightedList
from neighborly.core.ecs import (
    Active,
    EntityPrefab,
    GameObject,
    GameObjectFactory,
    World,
)
from neighborly.core.event import EventBuffer
from neighborly.core.relationship import (
    Relationship,
    RelationshipManager,
    Romance,
    add_relationship_status,
    get_relationship,
    get_relationships_with_statuses,
    has_relationship,
    remove_relationship_status,
)
from neighborly.core.settlement import Settlement
from neighborly.core.status import add_status
from neighborly.core.time import DAYS_PER_MONTH, SimDateTime
from neighborly.events import DepartEvent, StartBusinessEvent
from neighborly.utils.common import (
    add_business_to_settlement,
    add_residence_to_settlement,
    check_share_residence,
    end_job,
    set_residence,
    shutdown_business,
    spawn_business,
    spawn_residence,
    start_job,
)
from neighborly.utils.query import (
    are_related,
    has_family_to_care_of,
    has_work_experience_as,
    is_single,
)


class FindEmployment(GoalNode):
    __slots__ = "character", "world"

    def __init__(self, character: GameObject) -> None:
        super().__init__(SelectorBTNode([GetJob(character), StartBusiness(character)]))
        self.character = character
        self.world = character.world

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
        utilities = {self.character: 0.0}

        # Characters with families get plus one
        if has_family_to_care_of(self.character):
            utilities[self.character] += 1

        if self.character.has_component(Occupation):
            utilities[self.character] = 0
            return utilities

        if unemployed := self.character.get_component(Unemployed):
            months_unemployed = (
                unemployed.created - self.world.get_resource(SimDateTime)
            ).total_days / DAYS_PER_MONTH

            utilities[self.character] += months_unemployed / 6

        if virtues := self.character.try_component(Virtues):
            if virtues[Virtue.AMBITION] >= Virtues.AGREE:
                utilities[self.character] += 1
            if virtues[Virtue.RELIABILITY] >= Virtues.AGREE:
                utilities[self.character] += 1
            if virtues[Virtue.INDEPENDENCE] >= Virtues.AGREE:
                utilities[self.character] += 1

        # Divide the final score by the max possible score
        # jank? Yes.
        utilities[self.character] = utilities[self.character] / 5.0

        return utilities


class StartBusiness(GoalNode):
    __slots__ = "character", "world"

    def __init__(self, character: GameObject):
        super().__init__()
        self.character = character
        self.world = character.world

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
        utilities = {self.character: 1.0}

        # Characters with families get plus one
        if has_family_to_care_of(self.character):
            utilities[self.character] += 1

        if self.character.has_component(Occupation):
            utilities[self.character] = 0
            return utilities

        if unemployed := self.character.get_component(Unemployed):
            months_unemployed = (
                unemployed.created - self.world.get_resource(SimDateTime)
            ).total_days / DAYS_PER_MONTH

            utilities[self.character] += months_unemployed / 6

        if virtues := self.character.try_component(Virtues):
            if virtues[Virtue.AMBITION] >= Virtues.AGREE:
                utilities[self.character] += 1
            if virtues[Virtue.RELIABILITY] >= Virtues.AGREE:
                utilities[self.character] += 1
            if virtues[Virtue.INDEPENDENCE] >= Virtues.AGREE:
                utilities[self.character] += 1

        # Divide the final score by the max possible score
        # jank? Yes.
        utilities[self.character] = utilities[self.character] / 6.0

        return utilities

    def evaluate(self) -> NodeState:
        world = self.character.world
        current_settlement = self.character.get_component(CurrentSettlement)
        settlement = world.get_gameobject(current_settlement.settlement)
        settlement_comp = settlement.get_component(Settlement)
        event_buffer = world.get_resource(EventBuffer)
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

        event_buffer.append(
            StartBusinessEvent(
                world.get_resource(SimDateTime),
                self.character,
                business,
                owner_occupation_type.name,
            )
        )

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
        utilities = {self.character: 0.0}

        # Characters with families get plus one
        if has_family_to_care_of(self.character):
            utilities[self.character] += 1

        if self.character.has_component(Occupation):
            utilities[self.character] = 0
            return utilities

        if unemployed := self.character.get_component(Unemployed):
            months_unemployed = (
                unemployed.created - self.world.get_resource(SimDateTime)
            ).total_days / DAYS_PER_MONTH

            utilities[self.character] += months_unemployed / 6

        if virtues := self.character.try_component(Virtues):
            if virtues[Virtue.AMBITION] >= Virtues.AGREE:
                utilities[self.character] += 1
            if virtues[Virtue.RELIABILITY] >= Virtues.AGREE:
                utilities[self.character] += 1
            if virtues[Virtue.INDEPENDENCE] >= Virtues.AGREE:
                utilities[self.character] += 1

        # Divide the final score by the max possible score
        # jank? Yes.
        utilities[self.character] = utilities[self.character] / 5.0

        return utilities

    def is_complete(self) -> bool:
        return self.character.has_component(Occupation)

    def satisfied_goals(self) -> List[GoalNode]:
        return [FindEmployment(self.character)]

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, GetJob):
            return self.character == __o.character
        return False

    def evaluate(self) -> NodeState:
        for guid, (business, _) in self.world.get_components(
            (Business, OpenForBusiness)
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

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def get_utility(self) -> Dict[GameObject, float]:
        utilities: Dict[GameObject, float] = {self.character: 0}

        life_stage = self.character.get_component(LifeStage)

        if life_stage.life_stage == LifeStageType.Adult:
            utilities[self.character] = 0.9

        elif life_stage.life_stage == LifeStageType.YoungAdult:
            utilities[self.character] = 0.5

        if virtues := self.character.try_component(Virtues):
            if virtues[Virtue.INDEPENDENCE] >= Virtues.AGREE:
                utilities[self.character] += 0.1

        return utilities

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, FindOwnPlace):
            return self.character == __o.character
        return False


class FindVacantResidence(GoalNode):
    __slots__ = "character", "world"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.world: World = character.world

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def get_utility(self) -> Dict[GameObject, float]:
        return {self.character: 1}

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, FindVacantResidence):
            return self.character == __o.character
        return False

    def evaluate(self) -> NodeState:
        for guid, _ in self.world.get_components((Residence, Active, Vacant)):
            residence_obj = self.world.get_gameobject(guid)
            set_residence(self.character, residence_obj, True)
            return NodeState.SUCCESS

        return NodeState.FAILURE


class BuildNewHouse(GoalNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character

    def get_utility(self) -> Dict[GameObject, float]:
        return {self.character: 0.0}

    def satisfied_goals(self) -> List[GoalNode]:
        return [FindOwnPlace(self.character), FindVacantResidence(self.character)]

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, BuildNewHouse):
            return self.character == __o.character
        return False

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
            return NodeState.FAILURE

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(land_map.get_total_lots()) < 0.4:
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

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def get_utility(self) -> Dict[GameObject, float]:
        return {self.character: 1}

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, DepartSimulation):
            return self.character == __o.character
        return False

    def evaluate(self) -> NodeState:
        characters_to_depart: List[GameObject] = [self.character]

        # Have all spouses depart
        # Allows for polygamy
        spouses = get_relationships_with_statuses(self.character, Married)
        for relationship in spouses:
            rel = relationship.get_component(Relationship)
            spouse = self.world.get_gameobject(rel.target)
            if spouse.has_component(Active):
                characters_to_depart.append(spouse)

        # Have all children living in the same house depart
        children = get_relationships_with_statuses(self.character, ParentOf)
        for relationship in children:
            rel = relationship.get_component(Relationship)
            child = self.world.get_gameobject(rel.target)
            if child.has_component(Active) and check_share_residence(
                self.character, child
            ):
                characters_to_depart.append(child)

        for c in characters_to_depart:
            add_status(c, Departed())
            c.remove_component(Active)

        event = DepartEvent(
            self.world.get_resource(SimDateTime), characters_to_depart, ""
        )

        self.world.get_resource(EventBuffer).append(event)

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

# class GetMarried(GoalNode):
#     __slots__ = "character"
#
#     def __init__(self, character: GameObject) -> None:
#         super().__init__()
#         self.character: GameObject = character
#
#     def satisfied_goals(self) -> List[GoalNode]:
#         return []
#
#     def is_complete(self) -> bool:
#         return bool(get_relationships_with_statuses(self.character, Married))
#
#     def __eq__(self, __o: object) -> bool:
#         if isinstance(__o, GetMarried):
#             return self.character == __o.character
#         return False
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


class EndRelationship(GoalNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, EndRelationship):
            return self.character == __o.character
        return False

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def get_utility(self) -> Dict[GameObject, float]:
        utilities: Dict[GameObject, float] = {self.character: 0}

        rel_to_spouse = get_relationships_with_statuses(self.character, Dating)[0]

        romance = rel_to_spouse.get_component(Romance).get_value()

        utilities[self.character] += (-1.0 * romance) / 100

        if virtues := self.character.try_component(Virtues):
            if virtues[Virtue.ROMANCE] >= Virtues.STRONG_AGREE:
                utilities[self.character] += 1

        utilities[self.character] /= 2

        return utilities

    def evaluate(self) -> NodeState:
        ex_partner = self.character.world.get_gameobject(
            get_relationships_with_statuses(self.character, Dating)[0]
            .get_component(Relationship)
            .target
        )

        remove_relationship_status(self.character, ex_partner, Dating)
        remove_relationship_status(ex_partner, self.character, Dating)

        return NodeState.SUCCESS


class DivorceSpouse(GoalNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character

    def get_utility(self) -> Dict[GameObject, float]:
        utilities: Dict[GameObject, float] = {}

        rel_to_spouse = get_relationships_with_statuses(self.character, Married)[0]

        romance = rel_to_spouse.get_component(Romance).get_value()

        utilities[self.character] += (-1.0 * romance) / 100

        if virtues := self.character.try_component(Virtues):
            if virtues[Virtue.ROMANCE] >= Virtues.STRONG_AGREE:
                utilities[self.character] += 1

        utilities[self.character] /= 2

        return utilities

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def evaluate(self) -> NodeState:
        world = self.character.world
        ex_spouse = world.get_gameobject(
            get_relationships_with_statuses(self.character, Married)[0]
            .get_component(Relationship)
            .target
        )

        remove_relationship_status(self.character, ex_spouse, Married)
        remove_relationship_status(ex_spouse, self.character, Married)

        return NodeState.SUCCESS

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, DivorceSpouse):
            return self.character == __o.character
        return False


class Retire(GoalNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character = character

    def get_utility(self) -> Dict[GameObject, float]:
        utilities = {self.character: 0.0}

        occupation = self.character.get_component(Occupation)

        if self.character.get_component(LifeStage).life_stage < LifeStageType.Senior:
            utilities[self.character] -= 1
        else:
            utilities[self.character] += 1

        # This is a nested function. So, we call it once to return the
        # precondition function, then we call it a second time
        if has_work_experience_as(occupation.occupation_type, 10)(self.character):
            utilities[self.character] += 1

        utilities[self.character] = utilities[self.character] / 2.0

        return utilities

    def evaluate(self) -> NodeState:
        world = self.character.world
        add_status(self.character, Retired())

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

        romance_threshold = world.get_resource(NeighborlyConfig).settings.get(
            "dating_romance_threshold", 25
        )

        rel_to_initiator = get_relationship(self.target, self.initiator)

        romance = rel_to_initiator.get_component(Romance)

        if romance.get_value() < romance_threshold:
            return NodeState.FAILURE

        add_relationship_status(self.initiator, self.target, Dating())
        add_relationship_status(self.target, self.initiator, Dating())

        return NodeState.SUCCESS

    def get_utility(self) -> Dict[GameObject, float]:
        utilities: Dict[GameObject, float] = {self.initiator: 0, self.target: 0}

        if is_single(self.initiator):
            utilities[self.initiator] += 1
        else:
            utilities[self.initiator] -= 0.25

        if is_single(self.target):
            utilities[self.target] += 1
        else:
            utilities[self.target] -= 0.25

        if virtues := self.initiator.try_component(Virtues):
            if virtues[Virtue.ROMANCE] >= Virtues.AGREE:
                utilities[self.initiator] += 1

        if virtues := self.target.try_component(Virtues):
            if virtues[Virtue.ROMANCE] >= Virtues.AGREE:
                utilities[self.target] += 1

        world = self.initiator.world

        utilities[self.initiator] += (
            float(
                world.get_gameobject(
                    self.initiator.get_component(RelationshipManager).outgoing[
                        self.target.uid
                    ]
                )
                .get_component(Romance)
                .get_value()
            )
            / 100.0
        )

        if not is_single(self.initiator):
            utilities[self.initiator] -= 0.25

        utilities[self.target] += (
            float(
                world.get_gameobject(
                    self.target.get_component(RelationshipManager).outgoing[
                        self.initiator.uid
                    ]
                )
                .get_component(Romance)
                .get_value()
            )
            / 100.0
        )

        utilities[self.initiator] /= 3
        utilities[self.target] /= 3

        return utilities

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, AskOut):
            return self.initiator == __o.initiator and self.target == __o.target
        return False


class FindRomance(GoalNode):
    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character = character

    def get_utility(self) -> Dict[GameObject, float]:
        utilities: Dict[GameObject, float] = {self.character: 0}

        if not is_single(self.character):
            return {self.character: 0}
        else:
            utilities[self.character] += 1

        if life_stage := self.character.get_component(LifeStage):
            if life_stage.life_stage == LifeStageType.Adult:
                utilities[self.character] += 2
            elif life_stage.life_stage >= LifeStageType.YoungAdult:
                utilities[self.character] += 1

        if virtues := self.character.try_component(Virtues):
            if virtues[Virtue.ROMANCE] >= Virtues.AGREE:
                utilities[self.character] += 1

            if virtues[Virtue.LUST] >= Virtues.AGREE:
                utilities[self.character] += 1

        utilities[self.character] /= 5

        return utilities

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


class EndRomanceGoal(GoalNode):
    __slots__ = "initiator", "target"

    def __init__(self, initiator: GameObject, target: GameObject) -> None:
        super().__init__()
        self.initiator: GameObject = initiator
        self.target: GameObject = target

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def evaluate(self) -> NodeState:
        ...

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, EndRomanceGoal):
            return self.initiator == __o.initiator and self.target == __o.target
        return False
