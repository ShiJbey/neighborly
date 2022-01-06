import random
from typing import cast
import esper

from neighborly.core.character.character import GameCharacter
from neighborly.core.character.values import CharacterValues
from neighborly.core.relationship import Relationship
from neighborly.core.routine import Routine
import neighborly.core.behavior_utils as behavior_utils


class CharacterProcessor(esper.Processor):

    world: esper.World

    def process(self, *args, **kwargs):

        # date = behavior_utils.get_date(self.world)

        for character_id, character in self.world.get_component(GameCharacter):
            character = cast(GameCharacter, character)

            if character.location:
                location = behavior_utils.get_place(
                    self.world, character.location)

                # Socialize
                for other_character_id in location.characters_present:
                    if other_character_id == character_id:
                        continue

                    other_character = behavior_utils.get_character(
                        self.world, other_character_id)

                    if other_character_id not in character.relationships:
                        character.relationships[other_character_id] = Relationship(
                            character_id,
                            other_character_id,
                            CharacterValues.calculate_compatibility(
                                character.values, other_character.values),
                            other_character.gender == character.gender)
                    else:
                        character.relationships[other_character_id].progress_relationship(
                        )

                    if character_id not in other_character.relationships:
                        character.relationships[other_character_id] = Relationship(
                            other_character_id,
                            character_id,
                            CharacterValues.calculate_compatibility(
                                character.values, other_character.values),
                            other_character.gender == character.gender)
                    else:
                        other_character.relationships[character_id].progress_relationship(
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
                potential_locations = behavior_utils.get_locations(self.world)
                loc_id, _ = random.choice(potential_locations)
                behavior_utils.move_character(self.world, entity, loc_id)
