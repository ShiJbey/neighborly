from __future__ import annotations

from typing import Any, Dict

from ordered_set import OrderedSet

from neighborly.core.ecs import Component


class Residence(Component):
    """Residence is a place where characters live"""

    __slots__ = "owners", "former_owners", "residents", "former_residents", "_vacant"

    def __init__(self) -> None:
        super().__init__()
        self.owners: OrderedSet[int] = OrderedSet([])
        self.former_owners: OrderedSet[int] = OrderedSet([])
        self.residents: OrderedSet[int] = OrderedSet([])
        self.former_residents: OrderedSet[int] = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "owners": list(self.owners),
            "former_owners": list(self.former_owners),
            "residents": list(self.residents),
            "former_residents": list(self.former_residents),
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
        self.former_residents.add(resident)

    def is_resident(self, character: int) -> bool:
        """Return True if the given entity is a resident"""
        return character in self.residents


class Resident(Component):
    """Component attached to characters indicating that they live in the town"""

    __slots__ = "residence"

    def __init__(self, residence: int) -> None:
        super().__init__()
        self.residence: int = residence

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "residence": self.residence}
