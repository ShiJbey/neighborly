from __future__ import annotations

from typing import Any, Dict

from neighborly.core.ecs import (
    Component,
    EntityPrefab,
    GameObject,
    GameObjectFactory,
    ISerializable,
    World,
)


class ItemType(Component, ISerializable):
    """Tags a GameObject as being a definition of an item type."""

    def to_dict(self) -> Dict[str, Any]:
        return {}

    def __str__(self) -> str:
        return type(self).__name__

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class Item(Component, ISerializable):
    """Tags a GameObject as an instance of an item type."""

    __slots__ = "_item_type"

    _item_type: GameObject
    """The item type that this item is an instance of."""

    def __init__(self, item_type: GameObject) -> None:
        super().__init__()
        self._item_type = item_type

    @property
    def item_type(self) -> GameObject:
        return self._item_type

    def to_dict(self) -> Dict[str, Any]:
        return {"item_type": self.item_type.uid}


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


class ItemLibrary:
    """Manages runtime type information for items"""

    __slots__ = "_items"

    _items: Dict[str, GameObject]

    def __init__(self) -> None:
        self._items = {}

    @property
    def items(self) -> Dict[str, GameObject]:
        return self._items


def register_item_type(world: World, prefab: EntityPrefab) -> None:
    """Loads a new item type into the world's ItemLibrary."""
    factory = world.get_resource(GameObjectFactory)
    factory.add(prefab)
    item_type = factory.instantiate(world, prefab.name)
    item_type.name = prefab.name
    world.get_resource(ItemLibrary).items[item_type.name] = item_type
