"""Components for representing residential buildings.

"""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.components.settlement import District
from neighborly.ecs import Component


class ResidentialUnit(Component):
    """A Residence is a place where characters live."""

    __tablename__ = "residential_unit"

    building_id: Mapped[int] = mapped_column(ForeignKey("residential_building.uid"))
    building: Mapped[ResidentialBuilding] = relationship(
        foreign_keys=[building_id], back_populates="units"
    )
    """The building this unit is in."""
    residents: Mapped[Resident] = relationship(back_populates="residence")
    """All the characters who live at the residence (including non-owners)."""


class ResidentialBuilding(Component):
    """Tags a building as managing multiple residential units."""

    __tablename__ = "residential_building"

    district_id: Mapped[int] = mapped_column(ForeignKey("district.uid"))
    """The ID of the district this building is in."""
    district: Mapped[District] = relationship(foreign_keys=[district_id])
    """The district this building is in."""
    units: Mapped[list[ResidentialUnit]] = relationship(back_populates="building")
    """The residential units that belong to this building."""


class Resident(Component):
    """A Component attached to characters that tracks where they live."""

    __tablename__ = "resident"

    residence_id: Mapped[int] = mapped_column(ForeignKey("residential_unit.uid"))
    """The GameObject ID of their residence."""
    is_owner: Mapped[bool] = mapped_column(default=False)
    residence: Mapped[ResidentialUnit] = relationship(
        foreign_keys=[residence_id], back_populates="residents"
    )


class Vacant(Component):
    """Tags a residence that does not currently have anyone living there."""

    __tablename__ = "vacant"
