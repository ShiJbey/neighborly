from __future__ import annotations

from typing import Any, Dict

from ordered_set import OrderedSet

from neighborly.core.ecs import Component
from neighborly.core.status import StatusComponent


class Residence(Component):
    """A Residence is a place where characters live.

    Attributes
    ----------
    owners
        Characters that currently own the residence.
    residents
        All the characters who live at the residence (including non-owners).
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
        """Add owner to the residence."""
        self.owners.add(owner)

    def remove_owner(self, owner: int) -> None:
        """Remove owner from residence."""
        self.owners.remove(owner)

    def is_owner(self, character: int) -> bool:
        """Return True if the entity is an owner of this residence."""
        return character in self.owners

    def add_resident(self, resident: int) -> None:
        """Add a tenant to this residence."""
        self.residents.add(resident)

    def remove_resident(self, resident: int) -> None:
        """Remove a tenant rom this residence."""
        self.residents.remove(resident)

    def is_resident(self, character: int) -> bool:
        """Return True if the given entity is a resident."""
        return character in self.residents

    def __repr__(self) -> str:
        return f"Residence({self.to_dict()})"

    def __str__(self) -> str:
        return f"Residence({self.to_dict()})"


class Resident(StatusComponent):
    """A Component attached to characters that tracks where they live.

    Attributes
    ----------
    residence
       The GameObject ID of their residence.
    """

    __slots__ = "residence"

    def __init__(self, residence: int) -> None:
        """
        Parameters
        ----------
        residence
            The GameObject ID of their residence.
        """
        super().__init__()
        self.residence: int = residence

    def to_dict(self) -> Dict[str, Any]:
        return {"residence": self.residence}

    def __repr__(self) -> str:
        return f"Resident({self.to_dict()})"

    def __str__(self) -> str:
        return f"Resident({self.to_dict()})"


class Vacant(StatusComponent):
    """Tags a residence that does not currently have anyone living there."""

    pass
