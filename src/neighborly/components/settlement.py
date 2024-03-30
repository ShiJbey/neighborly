"""neighborly.settlement

This module contains classes and helper functions for defining and modeling settlements.

"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from neighborly.ecs import Component, GameData, GameObject


class DistrictData(GameData):
    """SQL queryable district component data."""

    __tablename__ = "districts"

    uid: Mapped[int] = mapped_column(
        ForeignKey("gameobjects.uid"), primary_key=True, unique=True
    )
    name: Mapped[str]
    settlement_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    population: Mapped[int]


class District(Component):
    """A subsection of a settlement."""

    __slots__ = (
        "data",
        "_description",
        "_settlement",
        "_residential_slots",
        "_business_slots",
        "_businesses",
        "_residences",
    )

    data: DistrictData
    """District"""
    _description: str
    """A short description of the district."""
    _settlement: GameObject
    """The settlement the district belongs to."""
    _residential_slots: int
    """The number of residential slots the district can build on."""
    _business_slots: int
    """The number of business slots the district can build on."""
    _businesses: list[GameObject]
    """Businesses in this district."""
    _residences: list[GameObject]
    """Residences in this district."""

    def __init__(
        self,
        gameobject: GameObject,
        name: str,
        description: str,
        settlement: GameObject,
        residential_slots: int,
        business_slots: int,
    ) -> None:
        super().__init__(gameobject)
        self.data = DistrictData(
            uid=gameobject.uid, name=name, population=0, settlement_id=settlement.uid
        )
        self._description = description
        self._settlement = settlement
        self._residential_slots = residential_slots
        self._business_slots = business_slots
        self._businesses = []
        self._residences = []

    @property
    def name(self) -> str:
        """The name of the settlement."""
        return self.data.name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the settlement"""

        self.data.name = value
        self.gameobject.name = value

        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

        if value:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.district.name!{value}"
            )
        else:
            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.district.name!{value}"
            )

    @property
    def description(self) -> str:
        """A short description of the district."""
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        """A short description of the district."""
        self._description = value

    @property
    def population(self) -> int:
        """The number of characters that live in this district."""
        return self.data.population

    @population.setter
    def population(self, value: int) -> None:
        """Set the number of characters that live in this district."""
        self.data.population = value

        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

    @property
    def settlement(self) -> GameObject:
        """The settlement the district belongs to."""
        return self._settlement

    @property
    def residential_slots(self) -> int:
        """Get the number of slots remaining for residential buildings."""
        return self._residential_slots

    @property
    def business_slots(self) -> int:
        """Get the number of slots remaining for businesses."""
        return self._business_slots

    @property
    def businesses(self) -> Iterable[GameObject]:
        """Get all the businesses in the district."""
        return self._businesses

    @property
    def residences(self) -> Iterable[GameObject]:
        """Get all the residential buildings in the district."""
        return self._residences

    def add_business(self, business: GameObject) -> None:
        """Add a business to this district.

        Parameters
        ---------
        business
            The business to add.
        """
        self._businesses.append(business)
        self._business_slots -= 1
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.district.businesses.{business.uid}"
        )

    def remove_business(self, business: GameObject) -> bool:
        """Remove a business from this district.

        Parameters
        ----------
        business
            The business to remove

        Returns
        -------
        bool
            True if the business was successfully removed, False otherwise.
        """
        try:
            self._businesses.remove(business)
            self._business_slots += 1
            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.district.businesses.{business.uid}"
            )
            return True
        except ValueError:
            # The business was not present
            return False

    def add_residence(self, residence: GameObject) -> None:
        """Add a residence to this district.

        Parameters
        ---------
        residence
            The district to add.
        """
        self._residences.append(residence)
        self._residential_slots -= 1
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.district.residences.{residence.uid}"
        )

    def remove_residence(self, residence: GameObject) -> bool:
        """Remove a residence from this district.

        Parameters
        ----------
        residence
            The residence to remove

        Returns
        -------
        bool
            True if the residence was successfully removed, False otherwise.
        """
        try:
            self._residences.remove(residence)
            self._residential_slots += 1
            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.district.residences.{residence.uid}"
            )
            return True
        except ValueError:
            # The residence was not present
            return False

    def on_add(self) -> None:
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.district.settlement!{self.settlement.uid}"
        )
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.district.name!{self.name}"
        )
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.district.population!{self.population}"
        )

    def on_remove(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.delete(self.data)

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.district")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self._description,
            "settlement": self._settlement.uid,
            "residences": [r.uid for r in self.residences],
            "businesses": [b.uid for b in self.businesses],
            "population": self.population,
        }


class SettlementData(GameData):
    """SQL queryable settlement component data."""

    __tablename__ = "settlements"

    uid: Mapped[int] = mapped_column(
        ForeignKey("gameobjects.uid"), primary_key=True, unique=True
    )
    name: Mapped[str]


class Settlement(Component):
    """A town, city, or village where characters live."""

    __slots__ = ("data", "_districts")

    data: SettlementData
    """Queryable settlement data."""
    _districts: list[GameObject]
    """References to districts within this settlement."""

    def __init__(
        self,
        gameobject: GameObject,
        name: str,
        districts: Optional[list[GameObject]] = None,
    ) -> None:
        super().__init__(gameobject)
        self.data = SettlementData(uid=gameobject.uid, name=name)
        self._districts = districts.copy() if districts is not None else []

    @property
    def name(self) -> str:
        """The name of the settlement."""
        return self.data.name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the settlement"""
        self.data.name = value
        self.gameobject.name = value

        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

        if value:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.settlement.name!{value}"
            )

    @property
    def population(self) -> int:
        """The total number of people living in the settlement."""
        total_population: int = 0

        for district in self._districts:
            total_population += district.get_component(District).population

        return total_population

    @property
    def districts(self) -> Iterable[GameObject]:
        """Return an iterable for this settlement's districts."""
        return self._districts

    def add_district(self, district: GameObject) -> None:
        """Add a district to this settlement.

        Parameters
        ---------
        district
            The district to add.
        """
        self._districts.append(district)
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.settlement.district.{district.uid}"
        )

    def remove_district(self, district: GameObject) -> bool:
        """Remove a district from this settlement.

        Parameters
        ----------
        district
            The district to remove

        Returns
        -------
        bool
            True if the district was successfully removed, False otherwise.
        """
        try:
            self._districts.remove(district)
            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.settlement.district.{district.uid}"
            )
            return True
        except ValueError:
            # The district was not present
            return False

    def on_add(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

        if self.name:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.settlement.name!{self.name}"
            )

    def on_remove(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.delete(self.data)

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.settlement")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "districts": [d.uid for d in self._districts],
            "population": self.population,
        }
