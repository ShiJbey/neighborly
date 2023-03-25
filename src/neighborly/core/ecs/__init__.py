"""
Entity-Component System

This package contains functionality for the entity-component system. It has definitions
for entities, systems, the world, queries, and entity prefabs.
"""

from .ecs import (
    Active,
    Component,
    ComponentNotFoundError,
    EntityPrefab,
    GameObject,
    GameObjectFactory,
    GameObjectNotFoundError,
    IComponentFactory,
    ISystem,
    ResourceNotFoundError,
    SystemGroup,
    World,
)
from .query import QB, Query, QueryFromFn, QueryGetFn

__all__ = [
    "Active",
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
    "GameObjectFactory",
]
