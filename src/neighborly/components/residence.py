from __future__ import annotations

from typing import Any, Dict

from ordered_set import OrderedSet

from neighborly.core.ecs import Component
from neighborly.core.status import StatusComponent


class Residence(Component):
    """
    Residence is a place where characters live

    Attributes
    ----------
    owners: OrderedSet[int]
        Characters that currently own the residence
    residents: OrderedSet[int]
        All the characters who live at the residence (including non-owners)
    """

    __slots__ = (
        "owners",
        "residents",
    )

    def __init__(self) -> None:
        super().__init__()
        self.owners: OrderedSet[int] = OrderedSet([])
        self.residents: OrderedSet[int] = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owners": list(self.owners),
            "residents": list(self.residents),
        }

    def add_owner(self, owner: int) -> None:
        """Add owner to the residence"""
        self.owners.add(owner)

    def remove_owner(self, owner: int) -> None:
        """Remove owner from residence"""
        self.owners.remove(owner)

    def is_owner(self, character: int) -> bool:
        """Return True if the entity is an owner of this residence"""
        return character in self.owners

    def add_resident(self, resident: int) -> None:
        """Add a tenant to this residence"""
        self.residents.add(resident)

    def remove_resident(self, resident: int) -> None:
        """Remove a tenant rom this residence"""
        self.residents.remove(resident)

    def is_resident(self, character: int) -> bool:
        """Return True if the given entity is a resident"""
        return character in self.residents


class Resident(StatusComponent):
    """
    Component attached to characters indicating that they live in the town

    Attributes
    ----------
    residence: int
        Unique ID of the Residence GameObject that the resident belongs to
    """

    __slots__ = "residence"

    def __init__(self, residence: int) -> None:
        super().__init__()
        self.residence: int = residence

    def to_dict(self) -> Dict[str, Any]:
        return {"residence": self.residence}


class Vacant(StatusComponent):
    """Tags a residence that does not currently have anyone living there"""

    pass
