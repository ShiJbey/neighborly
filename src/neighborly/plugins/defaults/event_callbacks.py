from typing import List

from neighborly.components.business import InTheWorkforce, Occupation
from neighborly.components.character import Departed
from neighborly.components.shared import Active
from neighborly.core.ecs import GameObject, World
from neighborly.core.event import Event
from neighborly.core.status import Status, add_status, remove_status
from neighborly.statuses.character import Unemployed
from neighborly.utils.business import end_job
from neighborly.utils.common import set_location, set_residence


def on_depart_callback(world: World, event: Event) -> None:
    character = world.get_gameobject(event["Character"])
    character.remove_component(Active)
    character.add_component(Departed())
    set_location(world, character, None)


def remove_retired_from_occupation(world: World, event: Event) -> None:
    character = world.get_gameobject(event["Retiree"])
    if character.has_component(Occupation):
        end_job(world, character, reason=event.name)


def remove_deceased_from_occupation(world: World, event: Event) -> None:
    character = world.get_gameobject(event["Character"])
    if character.has_component(Occupation):
        end_job(world, character, reason=event.name)


def remove_departed_from_occupation(world: World, event: Event) -> None:
    for gid in event.get_all("Character"):
        character = world.get_gameobject(gid)
        if character.has_component(Occupation):
            end_job(world, character, reason=event.name)


def remove_deceased_from_residence(world: World, event: Event) -> None:
    character = world.get_gameobject(event["Character"])
    set_residence(world, character, None)


def remove_departed_from_residence(world: World, event: Event) -> None:
    for gid in event.get_all("Character"):
        character = world.get_gameobject(gid)
        set_residence(world, character, None)


def on_become_young_adult(world: World, event: Event) -> None:
    """Enable employment for characters who are new young adults"""
    character = world.get_gameobject(event["Character"])
    character.add_component(InTheWorkforce())

    if not character.has_component(Occupation):
        add_status(world, character, Unemployed(336))


def remove_statuses_from_deceased(world: World, event: Event) -> None:
    """Remove all active statuses when characters die"""
    for c in event.get_all("Character"):
        character = world.get_gameobject(c)

        active_statuses: List[GameObject] = []
        for child_gameobject in character.children:
            if child_gameobject.has_component(Status):
                active_statuses.append(child_gameobject)

        for status in active_statuses:
            remove_status(character, status)


def remove_statuses_from_departed(world: World, event: Event) -> None:
    """Remove all active statuses when characters depart"""
    for c in event.get_all("Character"):
        character = world.get_gameobject(c)

        active_statuses: List[GameObject] = []
        for child_gameobject in character.children:
            if child_gameobject.has_component(Status):
                active_statuses.append(child_gameobject)

        for status in active_statuses:
            remove_status(character, status)
