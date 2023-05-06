"""
Entity-Component System

This package contains functionality for the entity-component system. It has definitions
for entities, systems, the world, queries, and entity prefabs.


"""

from .ecs import (
    Active,
    Component,
    ComponentAddedEvent,
    ComponentNotFoundError,
    ComponentRemovedEvent,
    EntityPrefab,
    Event,
    GameObject,
    GameObjectFactory,
    GameObjectNotFoundError,
    IComponentFactory,
    ISerializable,
    ISystem,
    ResourceNotFoundError,
    SystemGroup,
    World,
    EventListener,
)
from .query import QB, Query, QueryFromFn, QueryGetFn

__all__ = [
    "Active",
    "Component",
    "ComponentNotFoundError",
    "ComponentAddedEvent",
    "ComponentRemovedEvent",
    "Event",
    "EventListener",
    "GameObject",
    "GameObjectNotFoundError",
    "IComponentFactory",
    "ISerializable",
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
