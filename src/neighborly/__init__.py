"""Neighborly Character-Driven Social Simulation Framework."""

from neighborly.config import NeighborlyConfig
from neighborly.core.ecs import (
    Component,
    EntityPrefab,
    Event,
    GameObject,
    IComponentFactory,
    ISystem,
    SystemGroup,
    World,
)
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.__version__ import VERSION

__all__ = [
    "NeighborlyConfig",
    "Neighborly",
    "PluginInfo",
    "Component",
    "EntityPrefab",
    "GameObject",
    "ISystem",
    "SystemGroup",
    "World",
    "SimDateTime",
    "TimeDelta",
    "IComponentFactory",
    "Event",
    "VERSION",
]
