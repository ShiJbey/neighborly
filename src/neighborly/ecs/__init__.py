"""Neighborly ECS.

"""

from neighborly.ecs.component import Active, Component, TagComponent
from neighborly.ecs.event import Event
from neighborly.ecs.game_object import GameObject
from neighborly.ecs.system import System, SystemGroup
from neighborly.ecs.world import World

__all__ = [
    "Component",
    "TagComponent",
    "Active",
    "Event",
    "GameObject",
    "World",
    "System",
    "SystemGroup",
]
