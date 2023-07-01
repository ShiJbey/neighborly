from typing import Any

from neighborly.components.business import Occupation
from neighborly.components.character import (
    Dating,
    GameCharacter,
    LifeStage,
    LifeStageType,
    Married,
)
from neighborly.components.residence import Residence, Resident
from neighborly.core.ai.brain import Goals
from neighborly.core.ecs import Active, World
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
from neighborly.systems import System, GoalSuggestionSystemGroup
from neighborly.utils.query import is_single


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
    """
    Encourages senior residents to retire from their jobs
    """

    def on_update(self, world: World) -> None:
        for guid, (_, _, life_stage, _, goals) in world.get_components(
            (GameCharacter, Active, LifeStage, Occupation, Goals)
        ):
            if life_stage.life_stage == LifeStageType.Senior:
                character = world.gameobject_manager.get_gameobject(guid)
                goal = Retire(character)
                utility = goal.get_utility()[character]
                goals.push_goal(utility, goal)


plugin_info = PluginInfo(
    name="default systems plugin",
    plugin_id="default.systems",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    sim.world.system_manager.add_system(
        DatingBreakUpSystem(), system_group=GoalSuggestionSystemGroup
    )
    sim.world.system_manager.add_system(
        EndMarriageSystem(), system_group=GoalSuggestionSystemGroup
    )
    sim.world.system_manager.add_system(
        MarriageSystem(), system_group=GoalSuggestionSystemGroup
    )
    sim.world.system_manager.add_system(
        FindRomanceSystem(), system_group=GoalSuggestionSystemGroup
    )
    sim.world.system_manager.add_system(
        FindOwnPlaceSystem(), system_group=GoalSuggestionSystemGroup
    )
    sim.world.system_manager.add_system(
        RetirementSystem(), system_group=GoalSuggestionSystemGroup
    )
