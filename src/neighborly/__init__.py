"""Neighborly Character-Driven Social Simulation Framework.

Neighborly is an extensible, data-driven, agent-based modeling framework
designed to simulate towns of characters for games. It is intended to be a
tool for exploring simulationist approaches to character-driven emergent
narratives. Neighborly's simulation architecture is inspired by roguelikes
such as Caves of Qud and Dwarf Fortress.

"""

from neighborly.__version__ import VERSION
from neighborly.config import NeighborlyConfig
from neighborly.core.ecs import (
    Component,
    Event,
    GameObject,
    GameObjectPrefab,
    IComponentFactory,
    SystemBase,
    SystemGroup,
    World,
)
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.simulation import Neighborly, PluginInfo

__all__ = [
    "NeighborlyConfig",
    "Neighborly",
    "PluginInfo",
    "Component",
    "GameObjectPrefab",
    "GameObject",
    "SystemBase",
    "SystemGroup",
    "World",
    "SimDateTime",
    "TimeDelta",
    "IComponentFactory",
    "Event",
    "VERSION",
]
