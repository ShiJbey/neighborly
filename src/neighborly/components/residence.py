from __future__ import annotations

from typing import Any, Dict

from ordered_set import OrderedSet

from neighborly.core.ecs.ecs import Component, ISerializable
from neighborly.core.status import StatusComponent


class Residence(Component, ISerializable):
    """A Residence is a place where characters live."""

    __slots__ = (
        "owners",
        "residents",
    )

    owners: OrderedSet[int]
    """Characters that currently own the residence."""

    residents: OrderedSet[int]
    """All the characters who live at the residence (including non-owners)."""

    def __init__(self) -> None:
        super().__init__()
        self.owners = OrderedSet([])
        self.residents = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owners": list(self.owners),
            "residents": list(self.residents),
        }

    def add_owner(self, owner: int) -> None:
        """Add owner to the residence.

        Parameters
        ----------
        owner
            The GameObject ID of a residence owner.
        """
        self.owners.add(owner)

    def remove_owner(self, owner: int) -> None:
        """Remove owner from residence.

        Parameters
        ----------
        owner
            The GameObject ID of a residence owner.
        """
        self.owners.remove(owner)

    def is_owner(self, character: int) -> bool:
        """Check if a GameObject owns a residence.

        Parameters
        ----------
        character
            The GameObject ID of a residence owner.
        """
        return character in self.owners

    def add_resident(self, resident: int) -> None:
        """Add a tenant to this residence.

        Parameters
        ----------
        resident
            The GameObject ID of a resident.
        """
        self.residents.add(resident)

    def remove_resident(self, resident: int) -> None:
        """Remove a tenant rom this residence.

        Parameters
        ----------
        resident
            The GameObject ID of a resident.
        """
        self.residents.remove(resident)

    def is_resident(self, character: int) -> bool:
        """Check if a GameObject is a resident.

        Parameters
        ----------
        character
            The GameObject ID of a character
        """
        return character in self.residents

    def __repr__(self) -> str:
        return f"Residence({self.to_dict()})"

    def __str__(self) -> str:
        return f"Residence({self.to_dict()})"


class Resident(StatusComponent):
    """A Component attached to characters that tracks where they live."""

    __slots__ = "residence"

    residence: int
    """The GameObject ID of their residence."""

    def __init__(self, residence: int) -> None:
        """
        Parameters
        ----------
        residence
            The GameObject ID of their residence.
        """
        super().__init__()
        self.residence = residence

    def to_dict(self) -> Dict[str, Any]:
        return {"residence": self.residence}

    def __repr__(self) -> str:
        return f"Resident({self.to_dict()})"

    def __str__(self) -> str:
        return f"Resident({self.to_dict()})"


class Vacant(StatusComponent):
    """Tags a residence that does not currently have anyone living there."""

    pass
