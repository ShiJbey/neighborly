from neighborly.builtin import helpers
from neighborly.builtin.components import Active, Departed
from neighborly.builtin.helpers import set_location
from neighborly.core.business import Occupation
from neighborly.core.ecs import World
from neighborly.core.event import Event


def on_depart_callback(world: World, event: Event) -> None:
    character = world.get_gameobject(event["Character"])
    character.remove_component(Active)
    character.add_component(Departed())
    set_location(world, character, None)


def remove_retired_from_occupation(world: World, event: Event) -> None:
    character = world.get_gameobject(event["Character"])
    if character.has_component(Occupation):
        helpers.end_job(world, character, reason=event.name)


def remove_deceased_from_occupation(world: World, event: Event) -> None:
    character = world.get_gameobject(event["Character"])
    if character.has_component(Occupation):
        helpers.end_job(world, character, reason=event.name)


def remove_departed_from_occupation(world: World, event: Event) -> None:
    for gid in event.get_all("Character"):
        character = world.get_gameobject(gid)
        if character.has_component(Occupation):
            helpers.end_job(world, character, reason=event.name)


def remove_deceased_from_residence(world: World, event: Event) -> None:
    character = world.get_gameobject(event["Character"])
    helpers.set_residence(world, character, None)


def remove_departed_from_residence(world: World, event: Event) -> None:
    for gid in event.get_all("Character"):
        character = world.get_gameobject(gid)
        helpers.set_residence(world, character, None)
