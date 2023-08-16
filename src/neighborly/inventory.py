"""Neighborly's Inventory System.

This module contains classes definitions for components that help model items and
inventories. Item types are registered with the ECS like other prominent GameObject
types, and instantiated at the beginning of the simulation.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from neighborly.ecs import Component, GameObject, ISerializable, TagComponent, World


class ItemType(TagComponent, ABC):
    """Tags a GameObject as being a definition of an item type."""

    @classmethod
    @abstractmethod
    def instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        """Create an instance of this ItemType.

        Parameters
        ----------
        """
        raise NotImplementedError


class Item(Component, ISerializable):
    """Tags a GameObject as an instance of an item type."""

    __slots__ = "_item_type"

    _item_type: ItemType
    """The item type that this item is an instance of."""

    def __init__(self, item_type: ItemType) -> None:
        super().__init__()
        self._item_type = item_type

    @property
    def item_type(self) -> ItemType:
        return self._item_type

    def to_dict(self) -> Dict[str, Any]:
        return {"item_type": type(self.item_type).__name__}


class Inventory(Component, ISerializable):
    """Tracks the items currently held by a GameObject."""

    __slots__ = "_inventory"

    _inventory: Dict[GameObject, int]
    """Map of Items to quantities"""

    def __init__(self) -> None:
        super().__init__()
        self._inventory = {}

    def add_item(self, item: GameObject, quantity: int) -> None:
        """Add an item to the inventory.

        Parameters
        ----------
        item
            The item to add.
        quantity
            The amount to add to the inventory.
        """
        if item not in self._inventory:
            self._inventory[item] = 0
        self._inventory[item] += quantity

    def remove_item(self, item: GameObject, quantity: int) -> None:
        """Add an item to the inventory.

        Parameters
        ----------
        item
            The item to remove.
        quantity
            The quantity of the item to remove.
        """
        if item not in self._inventory:
            raise KeyError(f"Cannot find item, {item}, in inventory")

        if self._inventory[item] < quantity:
            raise ValueError(
                f"Quantity ({quantity}) too high. "
                f"Inventory has {self._inventory[item]} {item}(s)"
            )

        self._inventory[item] -= quantity
        if self._inventory[item] == 0:
            del self._inventory[item]

    def get_quantity(self, item: GameObject) -> int:
        """Returns the quantity of an item in the inventory.

        Parameters
        ----------
        item
            An item

        Returns
        -------
        int
            The number of the item present in the inventory
        """
        return self._inventory.get(item, 0)

    def to_dict(self) -> Dict[str, Any]:
        return {item.name: quantity for item, quantity in self._inventory.items()}

    def __str__(self) -> str:
        return self._inventory.__str__()

    def __repr__(self) -> str:
        items_by_name = {
            item.name: quantity for item, quantity in self._inventory.items()
        }
        return f"{type(self).__name__}({items_by_name.__repr__()})"


class BaseItem(ItemType, ABC):
    @classmethod
    def instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        item = world.gameobject_manager.spawn_gameobject()

        item_type = item.add_component(cls)
        item.add_component(Item, item_type=item_type)

        return item
