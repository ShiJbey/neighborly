from neighborly.core.ecs import GameObject
from neighborly.core.life_event import LifeEvent
from neighborly.core.time import SimDateTime
from neighborly.core.character import GameCharacter


def before_year(year: int):
    """
    Returns precondition function that checks if the
    current year is less than the given year
    """

    def precondition_fn(gameobject: GameObject, event: LifeEvent) -> bool:
        return gameobject.world.get_resource(SimDateTime).year < year

    return precondition_fn


def is_man(gameobject: GameObject, event: LifeEvent) -> bool:
    """Return true if GameObject is a man"""
    return "Male" in gameobject.get_component(GameCharacter).tags


def older_than(age: int):
    def precondition_fn(gameobject: GameObject, event: LifeEvent) -> bool:
        return gameobject.get_component(GameCharacter).age > age

    return precondition_fn


def print_msg(msg: str):
    def precondition_fn(gameobject: GameObject, event: LifeEvent) -> bool:
        print(msg)
        return True

    return precondition_fn
