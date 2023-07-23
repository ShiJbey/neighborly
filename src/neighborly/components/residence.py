"""Components for residence GameObjects and tracking residential status.

"""

from __future__ import annotations

from typing import Any, Dict

from ordered_set import OrderedSet

from neighborly.core.ecs import (
    Component,
    GameObject,
    GameObjectPrefab,
    ISerializable,
    World,
)
from neighborly.core.status import IStatus
from neighborly.spawn_table import ResidenceSpawnTable


class Residence(Component, ISerializable):
    """A Residence is a place where characters live."""

    __slots__ = (
        "owners",
        "residents",
    )

    owners: OrderedSet[GameObject]
    """Characters that currently own the residence."""

    residents: OrderedSet[GameObject]
    """All the characters who live at the residence (including non-owners)."""

    def __init__(self) -> None:
        super().__init__()
        self.owners = OrderedSet([])
        self.residents = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owners": [entry.uid for entry in self.owners],
            "residents": [entry.uid for entry in self.residents],
        }

    def add_owner(self, owner: GameObject) -> None:
        """Add owner to the residence.

        Parameters
        ----------
        owner
            A GameObject reference to a residence owner.
        """
        self.owners.add(owner)

    def remove_owner(self, owner: GameObject) -> None:
        """Remove owner from residence.

        Parameters
        ----------
        owner
            A GameObject reference to a residence owner.
        """
        self.owners.remove(owner)

    def is_owner(self, character: GameObject) -> bool:
        """Check if a GameObject owns a residence.

        Parameters
        ----------
        character
            A GameObject reference to a residence owner.
        """
        return character in self.owners

    def add_resident(self, resident: GameObject) -> None:
        """Add a tenant to this residence.

        Parameters
        ----------
        resident
            A GameObject reference to a resident.
        """
        self.residents.add(resident)

    def remove_resident(self, resident: GameObject) -> None:
        """Remove a tenant rom this residence.

        Parameters
        ----------
        resident
            A GameObject reference to a resident.
        """
        self.residents.remove(resident)

    def is_resident(self, character: GameObject) -> bool:
        """Check if a GameObject is a resident.

        Parameters
        ----------
        character
            A GameObject reference to a character
        """
        return character in self.residents

    def __repr__(self) -> str:
        return f"Residence({self.to_dict()})"

    def __str__(self) -> str:
        return f"Residence({self.to_dict()})"


class Resident(IStatus):
    """A Component attached to characters that tracks where they live."""

    __slots__ = "residence"

    residence: GameObject
    """The GameObject ID of their residence."""

    def __init__(self, year_created: int, residence: GameObject) -> None:
        """
        Parameters
        ----------
        year_created
            The year the character became a resident.
        residence
            A GameObject reference to their residence.
        """
        super().__init__(year_created)
        self.residence = residence

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "residence": self.residence.uid}

    def __repr__(self) -> str:
        return f"Resident({self.to_dict()})"

    def __str__(self) -> str:
        return f"Resident({self.to_dict()})"


class Vacant(IStatus):
    """Tags a residence that does not currently have anyone living there."""

    pass


def register_residence_prefab(world: World, prefab: GameObjectPrefab) -> None:
    """Registers a character prefab with the ECS and spawn tables."""

    # Add the prefab to the GameObject manager
    world.gameobject_manager.add_prefab(prefab)

    # Add an entry to the character spawn table
    world.resource_manager.get_resource(ResidenceSpawnTable).update(
        name=prefab.name,
        frequency=prefab.metadata.get("spawn_frequency", 0)
    )
