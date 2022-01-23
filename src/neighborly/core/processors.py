import random
from typing import cast

import esper

import neighborly.core.behavior_utils as behavior_utils
from neighborly.core.character.character import GameCharacter
from neighborly.core.character.values import CharacterValues
from neighborly.core.relationship import (
    Connection,
    Relationship,
    RelationshipModifier,
    get_modifier,
)
from neighborly.core.routine import Routine
from neighborly.core.time import HOURS_PER_YEAR


class CharacterProcessor(esper.Processor):
    world: esper.World

    def process(self, *args, **kwargs):

        delta_time: float = kwargs["delta_time"]

        # date = behavior_utils.get_date(self.world)

        for character_id, character in self.world.get_component(GameCharacter):
            character = cast(GameCharacter, character)

            if character.statuses.has_status("dead"):
                continue

            self._grow_older(character_id, character, delta_time)
            self._simulate_dating(character_id, character)

            if character.relationships.significant_other:
                self._simulate_breakup(character_id, character)

            self._socialize(character_id, character)

            if (
                character.age >= character.max_age
                and character.config.lifecycle.can_die
            ):
                self._die(character_id, character)

    def _grow_older(
        self, character_id: int, character: GameCharacter, hours: float
    ) -> None:
        """Increase the character's age and apply flags at major milestones"""
        if character.config.lifecycle.can_age:
            character.age += hours / HOURS_PER_YEAR

        if character.age > character.config.lifecycle.adult_age:
            character.statuses.add_status(AdultStatus())

    def _simulate_dating(self, character_id: int, character: GameCharacter) -> None:
        """Simulate the dating life of this person."""
        if character.relationships.significant_other:
            # Don't do anything if they are already dating someone
            return

        if character.age < character.config.lifecycle.marriageable_age:
            # They are too young to date
            return

        # Ask out one of the love interests
        love_interests = character.relationships.get_with_flags(
            Connection.LOVE_INTEREST
        )

        if not love_interests:
            return

        person_to_ask_id = random.choice(love_interests)
        person_to_ask = behavior_utils.get_character(self.world, person_to_ask_id)

        # They will accept if the other person is also one of their love interests
        if (
            character_id
            in person_to_ask.relationships.get_with_flags(Connection.LOVE_INTEREST)
            and person_to_ask.relationships.significant_other is not None
        ):
            character.statuses.add_status(DatingStatus(person_to_ask_id))
            character.relationships.significant_other = person_to_ask_id
            character.relationships[person_to_ask_id].add_modifier(
                get_modifier("significant other")
            )
            person_to_ask.statuses.add_status(DatingStatus(character_id))
            person_to_ask.relationships.significant_other = character_id
            person_to_ask.relationships[character_id].add_modifier(
                get_modifier("significant other")
            )

    def _simulate_breakup(self, character_id: int, character: GameCharacter) -> None:
        """Simulate the potential for divorce today in the course of this person's marriage."""
        # Check if this person is significantly more in love with someone else in town
        if character.relationships.significant_other:
            if not character.relationships[
                character.relationships.significant_other
            ].has_flags(Connection.LOVE_INTEREST):
                # Break up if dating
                if character.statuses.has_status("dating"):
                    partner_id = character.relationships.significant_other
                    partner = behavior_utils.get_character(self.world, partner_id)
                    partner.relationships.significant_other = None
                    partner.statuses.remove_status("dating")
                    partner.relationships[character_id].add_modifier(
                        RelationshipModifier(
                            "break up", salience=5, spark=-10, charge=-5
                        )
                    )
                    partner.relationships[character_id].remove_modifier(
                        get_modifier("significant other")
                    )

                    character.relationships.significant_other = None
                    character.statuses.remove_status("dating")
                    character.relationships[partner_id].add_modifier(
                        RelationshipModifier(
                            "break up", salience=5, spark=-10, charge=-5
                        )
                    )
                    character.relationships[partner_id].remove_modifier(
                        get_modifier("significant other")
                    )

    def _socialize(self, character_id: int, character: GameCharacter) -> None:
        """Have all the characters talk to those around them"""
        if character.location:
            location = behavior_utils.get_place(self.world, character.location)

            # Socialize
            for other_character_id in location.characters_present:
                if other_character_id == character_id:
                    continue

                other_character = behavior_utils.get_character(
                    self.world, other_character_id
                )

                if other_character_id not in character.relationships:
                    character.relationships[other_character_id] = Relationship(
                        character_id,
                        other_character_id,
                        CharacterValues.calculate_compatibility(
                            character.values, other_character.values
                        ),
                        other_character.gender == character.gender,
                        other_character.gender in character.attracted_to,
                    )
                else:
                    character.relationships.progress_relationship(other_character_id)

                if character_id not in other_character.relationships:
                    other_character.relationships[character_id] = Relationship(
                        other_character_id,
                        character_id,
                        CharacterValues.calculate_compatibility(
                            character.values, other_character.values
                        ),
                        other_character.gender == character.gender,
                        character.gender in other_character.attracted_to,
                    )
                else:
                    other_character.relationships.progress_relationship(character_id)

    def _die(self, character_id: int, character: GameCharacter) -> None:
        """Have a character pass away. Remove them from the simulation"""
        character.statuses.remove_status("alive")
        character.statuses.add_status(DeadStatus())


class RoutineProcessor(esper.Processor):
    world: esper.World

    def process(self, *args, **kwargs):
        del args
        del kwargs

        date = behavior_utils.get_date(self.world)

        for entity, (character, routine) in self.world.get_components(
            GameCharacter, Routine
        ):
            character = cast(GameCharacter, character)
            routine = cast(Routine, routine)

            activity = routine.get_activity(date.weekday_str, date.hour)

            if (
                activity
                and type(activity.location) == str
                and activity.location in character.location_aliases
            ):
                behavior_utils.move_character(
                    self.world,
                    entity,
                    character.location_aliases[str(activity.location)],
                )
            else:
                potential_locations = behavior_utils.get_locations(self.world)
                loc_id, _ = random.choice(potential_locations)
                behavior_utils.move_character(self.world, entity, loc_id)
