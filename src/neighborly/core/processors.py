import random
from typing import Optional, cast
import esper

from neighborly.core.character import GameCharacter
from neighborly.core.routine import Routine
import neighborly.core.behavior_utils as behavior_utils


class CharacterProcessor(esper.Processor):

    world: esper.World

    def process(self, *args, **kwargs):

        date = behavior_utils.get_date(self.world)

        for entity, character in self.world.get_component(GameCharacter):
            character = cast(GameCharacter, character)

            # Get routine
            routine: Routine = self.world.component_for_entity(entity, Routine)

            activity = routine.get_activity(date.weekday_str, date.hour)

            if activity:
                if str(activity.location) in character.location_aliases:
                    behavior_utils.move_character(
                        self.world, entity, character.location_aliases[str(activity.location)])
                else:
                    behavior_utils.move_character(
                        self.world, entity, int(activity.location))
            else:
                loc_id, location = random.choice(
                    behavior_utils.get_locations(self.world))

                behavior_utils.move_character(self.world, entity, loc_id)
