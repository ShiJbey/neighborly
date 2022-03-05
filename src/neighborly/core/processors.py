import random
from typing import cast, Optional

import neighborly.ai.behavior_utils as behavior_utils
from neighborly.core.character.character import GameCharacter
from neighborly.core.ecs import System, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationship
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime
from neighborly.core.town import Town


class CharacterProcessor(System):

    def process(self, *args, **kwargs):

        delta_time: float = kwargs["delta_time"]

        for _, character in self.world.get_component(GameCharacter):
            if not character.alive:
                continue

            self._grow_older(character, delta_time)
            self._socialize(self.world, character)

    def _grow_older(
            self, character: GameCharacter, hours: float
    ) -> None:
        """Increase the character's age and apply flags at major milestones"""
        if character.config.lifecycle.can_age:
            character.age += hours / HOURS_PER_YEAR

    def _socialize(self, world: World, character: GameCharacter) -> None:
        """Have all the characters talk to those around them"""
        if character.location:
            location = self.world.get_gameobject(character.location).get_component(Location)

            relationship_net = self.world.get_resource(RelationshipNetwork)

            character_id = character.gameobject.id

            # Socialize
            for other_character_id in location.characters_present:
                if other_character_id == character.gameobject.id:
                    continue

                if not relationship_net.has_connection(character_id, other_character_id):
                    relationship_net.add_connection(
                        character_id,
                        other_character_id,
                        Relationship(character_id, other_character_id, )
                    )
                    print(
                        f"{str(character.name)} met {str(world.get_gameobject(other_character_id).get_component(GameCharacter).name)}")
                else:
                    relationship_net.get_connection(character_id, other_character_id).update()

                if not relationship_net.has_connection(other_character_id, character_id):
                    relationship_net.add_connection(
                        other_character_id,
                        character_id,
                        Relationship(
                            other_character_id,
                            character_id,
                        )
                    )
                    print(
                        f"{str(world.get_gameobject(other_character_id).get_component(GameCharacter).name)} met {str(character.name)}")
                else:
                    relationship_net.get_connection(other_character_id, character_id).update()


class SocializeProcessor(System):
    """Runs logic for characters socializing with the other characters at their location"""

    def process(self, *args, **kwargs):
        for _, character in self.world.get_component(GameCharacter):
            if not character.alive:
                continue

            self._socialize(self.world, character)

    def _socialize(self, world: World, character: GameCharacter) -> None:
        """Have all the characters talk to those around them"""
        if character.location:
            location = self.world.get_gameobject(character.location).get_component(Location)

            relationship_net = self.world.get_resource(RelationshipNetwork)

            character_id = character.gameobject.id

            # Socialize
            for other_character_id in location.characters_present:
                if other_character_id == character.gameobject.id:
                    continue

                if not relationship_net.has_connection(character_id, other_character_id):
                    relationship_net.add_connection(
                        character_id,
                        other_character_id,
                        Relationship(character_id, other_character_id, )
                    )
                    print(
                        f"{str(character.name)} met {str(world.get_gameobject(other_character_id).get_component(GameCharacter).name)}")
                else:
                    relationship_net.get_connection(character_id, other_character_id).update()

                if not relationship_net.has_connection(other_character_id, character_id):
                    relationship_net.add_connection(
                        other_character_id,
                        character_id,
                        Relationship(
                            other_character_id,
                            character_id,
                        )
                    )
                    print(
                        f"{str(world.get_gameobject(other_character_id).get_component(GameCharacter).name)} met {str(character.name)}")
                else:
                    relationship_net.get_connection(other_character_id, character_id).update()


class RoutineProcessor(System):

    def process(self, *args, **kwargs):
        del args
        del kwargs

        date = self.world.get_resource(SimDateTime)

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
                if potential_locations:
                    loc_id, _ = random.choice(potential_locations)
                    behavior_utils.move_character(self.world, entity, loc_id)


class CityPlanner(System):
    """Responsible for adding residents to the town"""

    def process(self, *args, **kwargs) -> None:
        # Find an empty space to build a house
        residence = self.try_build_house()
        if residence is None:
            residence = self.try_get_abandoned()

        if residence is None:
            return

        # Create a new character to live at the location
        engine = self.world.get_resource(NeighborlyEngine)
        character = engine.create_character("default")
        self.world.add_gameobject(character)
        character.get_component(GameCharacter).location = residence.id
        character.get_component(GameCharacter).location_aliases['home'] = residence.id
        residence.get_component(Residence).add_tenant(character.id, True)
        residence.get_component(Location).characters_present.append(character.id)

    def try_build_house(self) -> Optional[GameObject]:
        town = self.world.get_resource(Town)
        engine = self.world.get_resource(NeighborlyEngine)
        if town.layout.has_vacancy():
            space = town.layout.allocate_space()
            place = engine.create_place("House")
            space.place_id = place.id
            place.get_component(Position2D).x = space.position[0]
            place.get_component(Position2D).y = space.position[1]
            self.world.add_gameobject(place)
            return place
        return None

    def try_get_abandoned(self) -> Optional[GameObject]:
        residences = list(filter(lambda res: res[1].is_vacant(), self.world.get_component(Residence)))
        if residences:
            return residences[0][1].gameobject
        return None
