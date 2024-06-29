"""Factories for relationship components.

"""

from typing import Any

from neighborly.components.relationship import RelationshipModifiers, Relationships
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
