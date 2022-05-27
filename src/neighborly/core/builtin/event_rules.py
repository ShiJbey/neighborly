from typing import cast
from neighborly.core.ecs import World
from neighborly.core.life_event import LifeEventRule
from neighborly.core.builtin.statuses import ElderStatus, AdultStatus
from neighborly.core.builtin.events import DeathEvent
from neighborly.core.time import SimDateTime
from neighborly.core.character import GameCharacter


def get_elder_characters(world: World, **kwargs):
    timestamp = world.get_resource(SimDateTime).to_iso_str()
    for gid, (character, _) in world.get_components(GameCharacter, ElderStatus):
        character = cast(GameCharacter, character)
        yield DeathEvent(timestamp, gid, str(character.name)), (character.gameobject,)


def get_adult_characters(world: World, **kwargs):
    timestamp = world.get_resource(SimDateTime).to_iso_str()
    for gid, (character, _) in world.get_components(GameCharacter, AdultStatus):
        character = cast(GameCharacter, character)
        yield DeathEvent(timestamp, gid, str(character.name)), (character.gameobject,)


death_event_rule = LifeEventRule(
    "Death",
    pattern_fn=get_elder_characters,
    probability=0.8,
)

depart_town_rule = LifeEventRule(
    "Depart",
    pattern_fn=get_adult_characters,
    probability=0.3,
)
