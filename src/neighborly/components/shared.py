"""Shared component types.

"""

from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from neighborly.ecs import Component, GameData, GameObject


class AgeData(GameData):
    """SQL queryable age component data."""

    __tablename__ = "ages"

    uid: Mapped[int] = mapped_column(
        ForeignKey("gameobjects.uid"), primary_key=True, unique=True
    )
    value: Mapped[float]


class Age(Component):
    """Tracks the age of a GameObject in years."""

    __slots__ = ("data",)

    data: AgeData
    """The age of the GameObject in simulated years."""

    def __init__(self, gameobject: GameObject, value: float = 0) -> None:
        super().__init__(gameobject)
        self.data = AgeData(uid=gameobject.uid, value=value)

    @property
    def value(self) -> float:
        """The age value."""
        return self.data.value

    @value.setter
    def value(self, value: float) -> None:
        """Set the age value."""

        self.data.value = value

        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.age.value")

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.age.value!{self.data.value}"
        )

    def on_add(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.age.value!{self.data.value}"
        )

    def on_remove(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.delete(self.data)

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.age")

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.data.value}
