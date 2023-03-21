from typing import Any, Optional

from neighborly.components.character import Dating, LifeStage, LifeStageType
from neighborly.components.shared import Active
from neighborly.core.ai.brain import Goals
from neighborly.core.ecs import GameObject
from neighborly.core.relationship import Relationship, RelationshipManager, Romance
from neighborly.plugins.defaults.actions import EndRomanceGoal, FindRomance
from neighborly.systems import System
from neighborly.utils.query import is_single


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
                owner.get_component(Goals).push_goal(1, EndRomanceGoal(owner, target))
                continue

            if love_interest := self._get_love_interest(owner):
                if love_interest != target:
                    owner.get_component(Goals).push_goal(
                        1, EndRomanceGoal(owner, target)
                    )
                    continue


class FindRomanceSystem(System):
    """
    Handles the dating/breakup loop

    This system is responsible for supplying characters with the goal to start dating or
    the goal to break up if they are already in a romantic relationship.
    """

    def run(self, *args: Any, **kwargs: Any) -> None:
        for guid, (goals, _, life_stage) in self.world.get_components(
            (Goals, Active, LifeStage)
        ):
            character = self.world.get_gameobject(guid)
            if (
                is_single(character)
                and life_stage.life_stage >= LifeStageType.Adolescent
            ):
                goals.push_goal(1, FindRomance(character))
