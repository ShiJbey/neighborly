"""neighborly.settlement

This module contains classes and helper functions for defining and modeling settlements.

"""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.ecs import Component


class Settlement(Component):
    """A town, city, or village where characters live."""

    __tablename__ = "settlement"

    districts: Mapped[list[District]] = relationship(back_populates="settlement")
    name: Mapped[str]
    population: Mapped[int] = mapped_column(default=0)

    def __str__(self) -> str:
        district_names = [d.name for d in self.districts]
        return f"Settlement(uid={self.uid!r}, name={self.name!r}, districts={district_names!r}, population={self.population!r})"

    def __repr__(self) -> str:
        district_names = [d.name for d in self.districts]
        return f"Settlement(uid={self.uid!r}, name={self.name!r}, districts={district_names!r}, population={self.population!r})"


class District(Component):
    """A subsection of a settlement."""

    __tablename__ = "district"

    name: Mapped[str]
    settlement_id: Mapped[int] = mapped_column(
        ForeignKey("settlement.uid"), nullable=True
    )
    settlement: Mapped[Settlement] = relationship(back_populates="districts")

    def __str__(self) -> str:
        return f"Settlement({self.uid=}, {self.name=}, {self.settlement.name=}"

    def __repr__(self) -> str:
        return f"Settlement({self.uid=}, {self.name=}, {self.settlement.name=}"
