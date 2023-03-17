from __future__ import annotations

import random
from typing import Dict, List, Optional

from neighborly.components import CurrentSettlement
from neighborly.components.business import (
    Business,
    BusinessOwner,
    Occupation,
    OpenForBusiness,
    Unemployed,
)
from neighborly.components.character import (
    LifeStage,
    LifeStageType,
    Retired,
    Virtue,
    Virtues,
)
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.content_management import OccupationTypeLibrary
from neighborly.core.ai.behavior_tree import NodeState, SelectorBTNode
from neighborly.core.ai.brain import GoalNode
from neighborly.core.ecs import EntityPrefab, GameObject, GameObjectFactory
from neighborly.core.ecs.ecs import World
from neighborly.core.event import EventBuffer
from neighborly.core.settlement import Settlement
from neighborly.core.time import DAYS_PER_MONTH, SimDateTime
from neighborly.events import StartBusinessEvent
from neighborly.utils.common import (
    add_business_to_settlement,
    end_job,
    shutdown_business,
    spawn_business,
    start_job,
)
from neighborly.utils.query import has_family_to_care_of, has_work_experience_as
from neighborly.utils.statuses import add_status


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
        # janky? Yes.
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
        # janky? Yes.
        utilities[self.character] = utilities[self.character] / 6.0

        return utilities

    def evaluate(self) -> NodeState:
        world = self.character.world
        current_settlement = self.character.get_component(CurrentSettlement)
        settlement = world.get_gameobject(current_settlement.settlement)
        settlement_comp = settlement.get_component(Settlement)
        event_buffer = world.get_resource(EventBuffer)
        occupation_types = world.get_resource(OccupationTypeLibrary)
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

        owner_occupation_type = occupation_types.get(owner_type)

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
        occupation_types = world.get_resource(OccupationTypeLibrary)
        rng = world.get_resource(random.Random)

        choices: List[EntityPrefab] = []
        weights: List[int] = []

        for prefab_name in business_spawn_table.get_eligible(settlement):
            prefab = GameObjectFactory.get(prefab_name)
            owner_type = prefab.components["Business"]["owner_type"]
            if owner_type:
                owner_occupation_type = occupation_types.get(owner_type)

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
        # janky? Yes.
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
        occupation_types = self.world.get_resource(OccupationTypeLibrary)

        for guid, (business, _) in self.world.get_components(
            (Business, OpenForBusiness)
        ):
            open_positions = business.get_open_positions()

            for occupation_name in open_positions:
                occupation_type = occupation_types.get(occupation_name)

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
                [FindVacantResidence(character), DepartSimulation(character)]
            )
        )
        self.character: GameObject = character

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()


class FindVacantResidence(GoalNode):

    __slots__ = "character", "world"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.world: World = character.world

    def satisfied_goals(self) -> List[GoalNode]:
        return []

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()


class DepartSimulation(GoalNode):

    __slots__ = "character", "world"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character: GameObject = character
        self.world: World = character.world

    def satisfied_goals(self) -> List[GoalNode]:
        return super().satisfied_goals()

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()


class StartFamily(GoalNode):
    ...


class GetMarried(GoalNode):
    ...


class FindSignificantOther(GoalNode):
    ...


class ProposeMarriage(GoalNode):
    ...


class HaveChildren(GoalNode):
    ...


class GetPregnant(GoalNode):
    ...


class BreakUp(GoalNode):
    ...


class DivorceSpouse(GoalNode):
    ...


class Retire(GoalNode):

    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character = character
        self.world = character.world

    def get_utility(self) -> Dict[GameObject, float]:
        utilities = {self.character: 0.0}

        occupation = self.character.get_component(Occupation)

        if self.character.get_component(LifeStage).life_stage < LifeStageType.Senior:
            utilities[self.character] -= 1
        else:
            utilities[self.character] += 1

        # This is a nested function so we call it once to return the
        # precondition function, then we call it a second time
        if has_work_experience_as(occupation.occupation_type, 10)(self.character):

            utilities[self.character] += 1

        utilities[self.character] = utilities[self.character] / 2.0

        return utilities

    def evaluate(self) -> NodeState:
        add_status(self.character, Retired())

        if business_owner := self.character.try_component(BusinessOwner):
            shutdown_business(self.world.get_gameobject(business_owner.business))
        else:
            end_job(self.character, "Retired")

        return NodeState.SUCCESS
