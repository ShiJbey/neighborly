from typing import cast
import itertools
from neighborly.core.ecs import World
from neighborly.core.life_event import LifeEventRule
from neighborly.core.builtin.statuses import ElderStatus, AdultStatus
from neighborly.core.builtin.events import DeathEvent, MarriageEvent
from neighborly.core.systems import LifeEventSystem
from neighborly.core.time import SimDateTime
from neighborly.core.character import GameCharacter


def get_elder_characters(world: World, **kwargs):
    for _, character in world.get_component(GameCharacter):
        if character.has_tag("Elder"):
            yield (character.gameobject,)


def get_adult_characters(world: World, **kwargs):
    for _, character in world.get_component(GameCharacter):
        if character.has_tag("Adult"):
            yield (character.gameobject,)


def get_single_adults(world: World, **kwargs):
    for _, character in world.get_component(GameCharacter):
        if character.has_tag("Adult") and not character.has_tag("In-Relationship"):
            yield (character.gameobject,)


def get_single_adult_pairs(world: World, **kwargs):
    single_adults = itertools.filterfalse(
        lambda c: c.has_tag("Adult") and not c.has_tag("In-Relationship"),
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
