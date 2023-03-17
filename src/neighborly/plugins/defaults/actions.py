"""
neighborly/plugins/defaults/actions

This holds implementations of Goals, Actions, and Systems that produce a default set of agent behavior.

This file contains implementations for:
- Finding romantic partners
- Ending romantic relationships
- Finding employment
- Retiring from employment
- Moving out of their parents home
"""


import random
from typing import Any, Dict, List, Optional

from neighborly import NeighborlyConfig
from neighborly.components import Active
from neighborly.components.character import (
    Dating,
    GameCharacter,
    LifeStage,
    LifeStageType,
)
from neighborly.core.ai import AIComponent
from neighborly.core.ai.behavior_tree import NodeState
from neighborly.core.ai.brain import ActionNode, GoalNode, WeightedActionList
from neighborly.core.ecs import GameObject
from neighborly.core.relationship import Relationship, RelationshipManager, Romance
from neighborly.systems import System
from neighborly.utils.query import are_related, is_single
from neighborly.utils.relationships import add_relationship_status, get_relationship


class AskOut(GoalNode):

    __slots__ = "initiator", "target"

    def __init__(self, initiator: GameObject, target: GameObject) -> None:
        super().__init__()
        self.initiator: GameObject = initiator
        self.target: GameObject = target

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


class FindPotentialLoveInterest(ActionNode):
    ...


class FindRomance(GoalNode):

    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character = character

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def evaluate(self) -> None:
        """Perform an action in-service of this goal"""

        world = self.character.world

        romance_threshold = world.get_resource(NeighborlyConfig).settings.get(
            "dating_romance_threshold", 25
        )

        # This character should try asking out another character
        candidates = [
            world.get_gameobject(c)
            for c in self.character.get_component(RelationshipManager).targets()
        ]

        actions = WeightedActionList(world.get_resource(random.Random))

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
            actions.pick_one().execute()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__, "character": self.character.uid}


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


class EndRomanceSystem(System):
    @staticmethod
    def _get_love_interest(character: GameObject) -> Optional[GameObject]:
        max_romance: int = -1
        love_interest: Optional[GameObject] = None

        for rel_id in character.get_component(RelationshipManager):
            relationship = character.world.get_gameobject(rel_id)

            romance = relationship.get_component(Romance).get_value()

            if romance > max_romance:
                max_romance = romance
                love_interest = character.world.get_gameobject(
                    relationship.get_component(Relationship).target
                )

        return love_interest

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, (relationship, _, romance) in self.world.get_components(
            (Relationship, Dating, Romance)
        ):
            # Check if they like someone else more or if they
            # dislike the person they are with
            owner = self.world.get_gameobject(relationship.owner)
            target = self.world.get_gameobject(relationship.target)

            if romance.get_value() <= -25:
                owner.get_component(AIComponent).push_goal(
                    1, EndRomanceGoal(owner, target)
                )
                continue

            if love_interest := self._get_love_interest(owner):
                if love_interest != target:
                    owner.get_component(AIComponent).push_goal(
                        1, EndRomanceGoal(owner, target)
                    )
                    continue


class FindRomanceSystem(System):
    """
    Handles the dating/breakup loop

    This system is responsible for supplying characters with the goal to start dating or the
    goal to break up if they are already in a romantic relationship.
    """

    def run(self, *args: Any, **kwargs: Any) -> None:
        for guid, (ai_component, _, life_stage) in self.world.get_components(
            (AIComponent, Active, LifeStage)
        ):
            character = self.world.get_gameobject(guid)
            if (
                is_single(character)
                and life_stage.life_stage >= LifeStageType.Adolescent
            ):
                ai_component.push_goal(1, FindRomance(character))
