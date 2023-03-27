from typing import Any

from neighborly.components import Occupation, Residence, Resident
from neighborly.components.character import (
    Dating,
    GameCharacter,
    LifeStage,
    LifeStageType,
    Married,
)
from neighborly.core.ai.brain import Goals
from neighborly.core.ecs import Active
from neighborly.core.relationship import Relationship
from neighborly.plugins.defaults.actions import (
    BreakUp,
    FindOwnPlace,
    FindRomance,
    GetDivorced,
    GetMarried,
    Retire,
)
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.systems import System
from neighborly.utils.query import is_single


class DatingBreakUpSystem(System):
    sys_group = "goal-suggestion"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, (relationship, _, _) in self.world.get_components(
            (Relationship, Dating, Active)
        ):
            owner = self.world.get_gameobject(relationship.owner)
            target = self.world.get_gameobject(relationship.target)
            goal = BreakUp(owner, target)
            utility = goal.get_utility().get(owner, 0)
            if utility > 0:
                owner.get_component(Goals).push_goal(utility, goal)


class MarriageSystem(System):
    sys_group = "goal-suggestion"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, (relationship, _, _) in self.world.get_components(
            (Relationship, Dating, Active)
        ):
            owner = self.world.get_gameobject(relationship.owner)
            target = self.world.get_gameobject(relationship.target)
            goal = GetMarried(owner, target)
            utility = goal.get_utility().get(owner, 0)
            if utility > 0:
                owner.get_component(Goals).push_goal(utility, goal)


class EndMarriageSystem(System):
    sys_group = "goal-suggestion"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, (relationship, _, _) in self.world.get_components(
            (Relationship, Married, Active)
        ):
            owner = self.world.get_gameobject(relationship.owner)
            target = self.world.get_gameobject(relationship.target)
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

    sys_group = "goal-suggestion"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for guid, (goals, _, life_stage) in self.world.get_components(
            (Goals, Active, LifeStage)
        ):
            character = self.world.get_gameobject(guid)
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

    sys_group = "goal-suggestion"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for guid, (_, _, life_stage, resident, goals) in self.world.get_components(
            (GameCharacter, Active, LifeStage, Resident, Goals)
        ):
            if (
                life_stage.life_stage == LifeStageType.Adult
                or life_stage.life_stage == LifeStageType.YoungAdult
            ):
                residence = self.world.get_gameobject(resident.residence).get_component(
                    Residence
                )
                if not residence.is_owner(guid):
                    character = self.world.get_gameobject(guid)
                    goal = FindOwnPlace(character)
                    utility = goal.get_utility()[character]
                    goals.push_goal(utility, goal)


class RetirementSystem(System):
    """
    Encourages senior residents to retire from their jobs
    """

    sys_group = "goal-suggestion"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for guid, (_, _, life_stage, _, goals) in self.world.get_components(
            (GameCharacter, Active, LifeStage, Occupation, Goals)
        ):
            if life_stage.life_stage == LifeStageType.Senior:
                character = self.world.get_gameobject(guid)
                goal = Retire(character)
                utility = goal.get_utility()[character]
                goals.push_goal(utility, goal)


plugin_info = PluginInfo(
    name="default systems plugin",
    plugin_id="default.systems",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    sim.add_system(DatingBreakUpSystem())
    sim.add_system(EndMarriageSystem())
    sim.add_system(MarriageSystem())
    sim.add_system(FindRomanceSystem())
    sim.add_system(FindOwnPlaceSystem())
    sim.add_system(RetirementSystem())
