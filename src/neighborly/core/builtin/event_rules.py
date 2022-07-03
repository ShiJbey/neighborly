from typing import cast
import itertools
from neighborly.core.ecs import World
from neighborly.core.life_event import LifeEventRule
from neighborly.core.builtin.statuses import Elder, Adult, InRelationship
from neighborly.core.builtin.events import DeathEvent, MarriageEvent
from neighborly.core.systems import LifeEventSystem
from neighborly.core.time import SimDateTime
from neighborly.core.character import GameCharacter


def get_elder_characters(world: World, **kwargs):
    for gid, _ in world.get_components(GameCharacter, Elder):
        yield (world.get_gameobject(gid),)


def get_adult_characters(world: World, **kwargs):
    for gid, _ in world.get_components(GameCharacter, Adult):
        yield (world.get_gameobject(gid),)


def get_single_adults(world: World, **kwargs):
    for _, character in world.get_component(GameCharacter):
        if character.gameobject.has_component(
            Adult
        ) and not character.gameobject.has_component(InRelationship):
            yield (character.gameobject,)


def get_single_adult_pairs(world: World, **kwargs):
    single_adults = itertools.filterfalse(
        lambda c: c.gameobject.has_component(Adult)
        and not c.gameobject.has_component(InRelationship),
        map(lambda res: res[1], world.get_component(GameCharacter)),
    )
    for pair in itertools.combinations(single_adults, 2):
        yield (pair[0].gameobject, pair[1].gameobject)


death_event_rule = LifeEventRule(
    "Death",
    pattern_fn=get_elder_characters,
    probability=0.8,
)

marriage_event_rule = LifeEventRule(
    "Marriage", pattern_fn=get_single_adult_pairs, probability=0.7
)

depart_town_rule = LifeEventRule(
    "Depart",
    pattern_fn=get_adult_characters,
    probability=0.3,
)


def load_event_rules() -> None:
    LifeEventSystem.register_event(death_event_rule)
    LifeEventSystem.register_event(marriage_event_rule)
    LifeEventSystem.register_event(depart_town_rule)
