import random
from typing import Optional, cast
import esper

from neighborly.core.character import GameCharacter
from neighborly.core.relationship import Relationship
from neighborly.core.routine import Routine
import neighborly.core.behavior_utils as behavior_utils


class CharacterProcessor(esper.Processor):

    world: esper.World

    def process(self, *args, **kwargs):

        date = behavior_utils.get_date(self.world)

        for character_id, character in self.world.get_component(GameCharacter):
            character = cast(GameCharacter, character)

            if character.location:
                location = behavior_utils.get_place(
                    self.world, character.location)

                # Socialize
                for other_character_id in location.characters_present:
                    if other_character_id == character_id:
                        continue
                    if other_character_id not in character.relationships:
                        other_character = behavior_utils.get_character(
                            self.world, other_character_id)
                        character.relationships[other_character_id] = Relationship(
                            character_id, other_character_id, 0, other_character.gender == character.gender)
                    else:
                        character.relationships[other_character_id].progress_relationship(
                        )


class RoutineProcessor(esper.Processor):

    world: esper.World

    def process(self, *args, **kwargs):

        date = behavior_utils.get_date(self.world)

        for entity, (character, routine) in self.world.get_components(GameCharacter, Routine):
            character = cast(GameCharacter, character)
            routine = cast(Routine, routine)

            activity = routine.get_activity(date.weekday_str, date.hour)

            if activity and type(activity.location) == str and activity.location in character.location_aliases:
                behavior_utils.move_character(
                    self.world, entity, character.location_aliases[str(activity.location)])
            else:
                loc_id, location = random.choice(
                    behavior_utils.get_locations(self.world))

                behavior_utils.move_character(self.world, entity, loc_id)
