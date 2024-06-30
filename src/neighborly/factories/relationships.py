"""Factories for relationship components.

"""

from typing import Any

from neighborly.components.relationship import (
    IsSingle,
    KeyRelations,
    RelationshipModifiers,
    Relationships,
)
from neighborly.ecs import Component, ComponentFactory, World


class RelationshipsFactory(ComponentFactory):
    """Creates instances of Relationships components."""

    __component__ = "Relationships"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return Relationships()


class RelationshipModifiersFactory(ComponentFactory):
    """Creates Modifiers component instances."""

    __component__ = "RelationshipModifiers"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return RelationshipModifiers()


class KeyRelationsFactory(ComponentFactory):
    """Creates KeyRelations component instances."""

    __component__ = "KeyRelations"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return KeyRelations()


class IsSingleFactory(ComponentFactory):
    """Creates IsSingle component instances."""

    __component__ = "IsSingle"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return IsSingle()
