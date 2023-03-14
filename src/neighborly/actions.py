import random
from typing import Any, Dict, List, Optional

from neighborly.components import CurrentSettlement
from neighborly.components.business import (
    Business,
    BusinessOwner,
    Occupation,
    OpenForBusiness,
)
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.content_management import OccupationTypeLibrary
from neighborly.core.ai import Action, Goal
from neighborly.core.ai.brain import GoalStack
from neighborly.core.ecs import EntityPrefab, GameObject, GameObjectFactory
from neighborly.core.event import EventBuffer
from neighborly.core.settlement import Settlement
from neighborly.core.time import SimDateTime
from neighborly.events import StartBusinessEvent
from neighborly.utils.common import (
    add_business_to_settlement,
    spawn_business,
    start_job,
)


class FindEmploymentGoal(Goal):

    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character = character

    def is_complete(self) -> bool:
        return self.character.has_component(Occupation)

    def take_action(self, goal_stack: GoalStack) -> None:
        GetJobAction(self.character)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__, "character": self.character.uid}


class GetJobAction(Action):
    def __init__(self, owner: GameObject) -> None:
        super().__init__()
        self.owner: GameObject = owner
        self.world = owner.world

    def execute(self) -> bool:
        occupation_types = self.world.get_resource(OccupationTypeLibrary)

        for guid, (business, _) in self.world.get_components(
            (Business, OpenForBusiness)
        ):
            open_positions = business.get_open_positions()

            for occupation_name in open_positions:
                occupation_type = occupation_types.get(occupation_name)

                if occupation_type.passes_preconditions(self.owner):
                    start_job(
                        self.owner, self.world.get_gameobject(guid), occupation_name
                    )
                    return True

        return False


class StartBusinessGoal(Goal):

    __slots__ = "character"

    def __init__(self, character: GameObject) -> None:
        super().__init__()
        self.character = character

    def is_complete(self) -> bool:
        return self.character.has_component(BusinessOwner)

    def take_action(self, goal_stack: GoalStack) -> None:
        action = StartBusinessAction(self.character)
        action.execute()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__, "character": self.character.uid}


class StartBusinessAction(Action):

    __slots__ = "character"

    def __init__(self, character: GameObject):
        super().__init__()
        self.character = character

    def execute(self) -> bool:
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
            return False

        vacancies = settlement_comp.land_map.get_vacant_lots()

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return False

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

        return True

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
