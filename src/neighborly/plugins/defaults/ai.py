"""
Default implementations of AI modules
"""
import random
from typing import Any, List, Optional

from neighborly.components.routine import Routine
from neighborly.components.shared import Location, LocationAliases, OpenToPublic
from neighborly.content_management import AIBrainLibrary
from neighborly.core.action import Action
from neighborly.core.ai.brain import IAIBrain
from neighborly.core.ecs import GameObject, World
from neighborly.core.life_event import ActionableLifeEvent
from neighborly.core.time import SimDateTime
from neighborly.simulation import Neighborly, PluginInfo


class DefaultMovementModule:
    def get_next_location(self, world: World, gameobject: GameObject) -> Optional[int]:
        date = world.get_resource(SimDateTime)
        routine = gameobject.try_component(Routine)
        location_aliases = gameobject.try_component(LocationAliases)

        if routine:
            routine_entry = routine.get_entry(date.weekday, date.hour)

            if (
                routine_entry
                and isinstance(routine_entry.location, str)
                and location_aliases
            ):
                return location_aliases.aliases[routine_entry.location]

            elif routine_entry:
                return int(routine_entry.location)

        potential_locations: List[int] = [
            res[0] for res in world.get_components((Location, OpenToPublic))
        ]

        if potential_locations:
            return world.get_resource(random.Random).choice(potential_locations)

        return None


# class DefaultSocialAIModule:
#     def get_next_action(
#         self, world: World, character: GameObject
#     ) -> Optional[Action]:
#         current_location_comp = character.try_component(CurrentLocation)

#         if current_location_comp is None:
#             return None

#         current_location = world.get_gameobject(current_location_comp.location)

#         available_actions = current_location.try_component(AvailableActions)

#         other_character = world.get_gameobject(
#             world.get_resource(random.Random).choice(
#                 list(current_location.get_component(Location).entities)
#             )
#         )

#         if available_actions is None:
#             return None

#         for action in available_actions.actions:
#             if action_instance := action.instantiate(world, character, other_character):
#                 return action_instance

#         return None


class DefaultBrain(IAIBrain):
    def __init__(self) -> None:
        super().__init__()
        self.life_events: List[ActionableLifeEvent] = []
        self.actions: List[Action] = []

    def get_type(self) -> str:
        return self.__class__.__name__

    def get_next_location(self, world: World, gameobject: GameObject) -> Optional[int]:
        pass

    def execute_action(self, world: World, gameobject: GameObject) -> None:
        rng = world.get_resource(random.Random)
        if self.actions:
            chosen_action = rng.choice(self.actions)
            if chosen_action.is_valid(world):
                chosen_action.execute()
        self.actions.clear()

    def append_action(self, action: Action) -> None:
        self.actions.append(action)

    def append_life_event(self, event: ActionableLifeEvent) -> None:
        self.life_events.append(event)

    def select_life_event(self, world: World) -> Optional[ActionableLifeEvent]:
        rng = world.get_resource(random.Random)
        if self.life_events:
            chosen = rng.choice(self.life_events)
            if chosen.is_valid(world):
                return chosen

        return None


plugin_info = PluginInfo(
    name="default ai plugin",
    plugin_id="default.ai",
    version="0.1.0",
)


def default_brain_factory(**kwargs: Any) -> IAIBrain:
    return DefaultBrain()


def setup(sim: Neighborly, **kwargs: Any):
    sim.world.get_resource(AIBrainLibrary).add("default", default_brain_factory)
