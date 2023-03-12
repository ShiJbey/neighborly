"""
Default implementations of AI modules
"""
import random
from typing import Any, List, Optional

from neighborly.components.routine import Routine
from neighborly.components.shared import Location, LocationAliases, OpenToPublic
from neighborly.core.ecs import GameObject, World
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


plugin_info = PluginInfo(
    name="default ai plugin",
    plugin_id="default.ai",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    pass
