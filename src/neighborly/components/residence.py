"""Components for representing residential buildings.

"""

from __future__ import annotations

from typing import Any, Iterable

from ordered_set import OrderedSet

from neighborly.ecs import Component, GameObject, TagComponent


class ResidentialUnit(Component):
    """A Residence is a place where characters live."""

    __slots__ = "_owners", "_residents", "_building"

    _building: GameObject
    """The building this unit is in."""
    _owners: OrderedSet[GameObject]
    """Characters that currently own the residence."""
    _residents: OrderedSet[GameObject]
    """All the characters who live at the residence (including non-owners)."""

    def __init__(self, building: GameObject) -> None:
        super().__init__()
        self._building = building
        self._owners = OrderedSet([])
        self._residents = OrderedSet([])

    @property
    def building(self) -> GameObject:
        """Get the building the residential unit is in."""
        return self._building

    @property
    def owners(self) -> Iterable[GameObject]:
        """Get the owners of the residence."""
        return self._owners

    @property
    def residents(self) -> Iterable[GameObject]:
        """Get all the residents of the residence."""
        return self._residents

    def to_dict(self) -> dict[str, Any]:
        return {
            "building": self.building.uid,
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
        self._owners.add(owner)

    def remove_owner(self, owner: GameObject) -> None:
        """Remove owner from residence.

        Parameters
        ----------
        owner
            A GameObject reference to a residence owner.
        """
        self._owners.remove(owner)

    def is_owner(self, character: GameObject) -> bool:
        """Check if a GameObject owns a residence.

        Parameters
        ----------
        character
            A GameObject reference to a residence owner.
        """
        return character in self._owners

    def add_resident(self, resident: GameObject) -> None:
        """Add a tenant to this residence.

        Parameters
        ----------
        resident
            A GameObject reference to a resident.
        """
        self._residents.add(resident)

    def remove_resident(self, resident: GameObject) -> None:
        """Remove a tenant rom this residence.

        Parameters
        ----------
        resident
            A GameObject reference to a resident.
        """
        self._residents.remove(resident)

    def is_resident(self, character: GameObject) -> bool:
        """Check if a GameObject is a resident.

        Parameters
        ----------
        character
            A GameObject reference to a character
        """
        return character in self._residents

    def __repr__(self) -> str:
        return f"Residence({self.to_dict()})"

    def __str__(self) -> str:
        return f"Residence({self.to_dict()})"

    def __len__(self) -> int:
        return len(self._residents)


class ResidentialBuilding(Component):
    """Tags a building as managing multiple residential units."""

    __slots__ = ("_residential_units",)

    _residential_units: list[GameObject]
    """The residential units that belong to this building."""

    def __init__(self) -> None:
        super().__init__()
        self._residential_units = []

    @property
    def units(self) -> Iterable[GameObject]:
        """Get the residential units within the building."""
        return self._residential_units

    def add_residential_unit(self, residence: GameObject) -> None:
        """Add a residential unit to the building."""
        self._residential_units.append(residence)

    def remove_residential_unit(self, residence: GameObject) -> None:
        """Add a residential unit to the building."""
        self._residential_units.remove(residence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "units": [u.uid for u in self._residential_units],
        }


class Resident(Component):
    """A Component attached to characters that tracks where they live."""

    __slots__ = (
        "settlement",
        "district",
        "building",
        "residence",
    )

    settlement: GameObject
    """The settlement they live in."""
    district: GameObject
    """The district they live in."""
    building: GameObject
    """The residential building they live in."""
    residence: GameObject
    """The unit they live in within the building."""

    def __init__(
        self,
        settlement: GameObject,
        district: GameObject,
        building: GameObject,
        residence: GameObject,
    ) -> None:
        """
        Parameters
        ----------
        residence
            A GameObject reference to their residence.
        """
        super().__init__()
        self.settlement = settlement
        self.district = district
        self.building = building
        self.residence = residence

    def to_dict(self) -> dict[str, Any]:
        return {
            "residence": self.residence.uid,
            "building": self.building.uid,
            "district": self.district.uid,
            "settlement": self.settlement.uid,
        }

    def __repr__(self) -> str:
        return f"Resident({self.to_dict()})"

    def __str__(self) -> str:
        return f"Resident({self.to_dict()})"


class Vacant(TagComponent):
    """Tags a residence that does not currently have anyone living there."""
