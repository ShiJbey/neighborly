"""
Entity-Component System

This package contains functionality for the entity-component system. It has definitions
for entities, systems, the world, queries, and entity prefabs.
"""

from .ecs import (
    Component,
    ComponentNotFoundError,
    GameObject,
    GameObjectNotFoundError,
    IComponentFactory,
    ISystem,
    ResourceNotFoundError,
    SystemGroup,
    World,
)
from .prefab import EntityPrefab
from .query import QB, Query, QueryFromFn, QueryGetFn

__all__ = [
    "Component",
    "ComponentNotFoundError",
    "GameObject",
    "GameObjectNotFoundError",
    "IComponentFactory",
    "ISystem",
    "SystemGroup",
    "ResourceNotFoundError",
    "World",
    "EntityPrefab",
    "Query",
    "QB",
    "QueryFromFn",
    "QueryGetFn",
]
