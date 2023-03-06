import random
from typing import List, Optional

from neighborly.components import Active, CurrentSettlement, InTheWorkforce, Unemployed
from neighborly.content_management import BusinessLibrary, OccupationTypeLibrary
from neighborly.core.action import Action
from neighborly.core.ecs import GameObject, World
from neighborly.core.event import EventBuffer
from neighborly.core.roles import RoleList
from neighborly.core.settlement import Settlement
from neighborly.core.time import SimDateTime
from neighborly.events import StartBusinessEvent
from neighborly.prefabs import BusinessPrefab
from neighborly.utils.common import (
    add_business_to_settlement,
    spawn_business,
    start_job,
)


class StartBusinessAction(Action):
    initiator = "Character"

    def __init__(self, date: SimDateTime, character: GameObject):
        super().__init__(timestamp=date, roles={"Character": character})

    def execute(self) -> bool:
        character = self["Character"]
        world = character.world
        current_settlement = character.get_component(CurrentSettlement)
        settlement = world.get_gameobject(current_settlement.settlement)
        settlement_comp = settlement.get_component(Settlement)
        event_buffer = world.get_resource(EventBuffer)
        occupation_types = world.get_resource(OccupationTypeLibrary)
        rng = world.get_resource(random.Random)

        # Get all the eligible business prefabs that are eligible for building
        # and the character meets the requirements for the owner occupation
        business_prefab = self._get_business_character_can_own(character)

        if business_prefab is None:
            return False

        vacancies = settlement_comp.land_map.get_vacant_lots()

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return False

        # Pick a random lot from those available
        lot = rng.choice(vacancies)

        owner_type = business_prefab.get_owner_type()

        assert owner_type

        owner_occupation_type = occupation_types.get(owner_type)

        business = spawn_business(world, business_prefab)

        add_business_to_settlement(
            business,
            world.get_gameobject(settlement.uid),
            lot_id=lot,
        )

        event_buffer.append(
            StartBusinessEvent(
                world.get_resource(SimDateTime),
                character,
                business,
                owner_occupation_type.name,
            )
        )

        start_job(character, business, owner_occupation_type.name, is_owner=True)

        return True

    @staticmethod
    def _get_business_character_can_own(
        character: GameObject,
    ) -> Optional[BusinessPrefab]:
        world = character.world
        current_settlement = character.get_component(CurrentSettlement)
        settlement = world.get_gameobject(current_settlement.settlement)
        business_library = world.get_resource(BusinessLibrary)
        occupation_types = world.get_resource(OccupationTypeLibrary)
        rng = world.get_resource(random.Random)

        choices: List[BusinessPrefab] = []
        weights: List[int] = []

        for prefab in business_library.get_eligible(settlement):
            if prefab.get_owner_type():
                owner_occupation_type = occupation_types.get(prefab.get_owner_type())

                if owner_occupation_type.passes_preconditions(character):
                    choices.append(prefab)
                    weights.append(prefab.spawn_frequency)

        if choices:
            # Choose an archetype at random
            return rng.choices(population=choices, weights=weights, k=1)[0]

        return None

    @classmethod
    def instantiate(cls, world: World, bindings: RoleList) -> Optional[Action]:
        rng = world.get_resource(random.Random)

        if bindings:
            candidates = [bindings[cls.initiator]]
        else:
            candidates = [
                world.get_gameobject(g)
                for g, _ in world.get_components((InTheWorkforce, Active, Unemployed))
            ]

        if not candidates:
            return None

        # NOTE: It might be nice to eventually swap this out for a
        # selection strategy that scores the characters based on
        # who is most likely to take on this role
        candidate = rng.choice(candidates)

        return cls(world.get_resource(SimDateTime), candidate)
