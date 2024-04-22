"""Business Components.

This module contains class definitions for components and classes that model businesses
in the settlement and character occupations.

"""

from __future__ import annotations

import enum
from typing import Any, Iterable, Mapping, Optional

from sqlalchemy import ForeignKey, delete
from sqlalchemy.orm import Mapped, mapped_column

from neighborly.datetime import SimDate
from neighborly.ecs import Component, GameData, GameObject
from neighborly.effects.base_types import Effect
from neighborly.preconditions.base_types import Precondition


class OccupationData(GameData):
    """SQL Data for an occupation."""

    __tablename__ = "occupations"

    uid: Mapped[int] = mapped_column(
        ForeignKey("gameobjects.uid"), primary_key=True, unique=True
    )
    role_id: Mapped[str]
    business_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    start_date: Mapped[int]


class Occupation(Component):
    """Information about a character's employment status."""

    __slots__ = "_start_date", "_business", "_job_role"

    _job_role: JobRole
    """The job role."""
    _business: GameObject
    """The business they work for."""
    _start_date: SimDate
    """The year they started this occupation."""

    def __init__(
        self,
        gameobject: GameObject,
        job_role: JobRole,
        business: GameObject,
        start_date: SimDate,
    ) -> None:
        """
        Parameters
        ----------
        job_role
            The job role associated with this occupation.
        business
            The business that the character is work for.
        start_date
            The date they started this occupation.
        """
        super().__init__(gameobject)
        self._job_role = job_role
        self._business = business
        self._start_date = start_date

    @property
    def job_role(self) -> JobRole:
        """The job role."""
        return self._job_role

    @property
    def business(self) -> GameObject:
        """The business they work for."""
        return self._business

    @property
    def start_date(self) -> SimDate:
        """The year they started this occupation."""
        return self._start_date

    def on_add(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.add(
                OccupationData(
                    uid=self.gameobject.uid,
                    role_id=self.job_role.definition_id,
                    business_id=self.business.uid,
                    start_date=self.start_date.to_iso_str(),
                )
            )

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.occupation.job_role!{self.job_role.definition_id}"
        )
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.occupation.business!{self.business.uid}"
        )
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.occupation.start_date!{self.start_date}"
        )

    def on_remove(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.execute(
                delete(OccupationData).where(OccupationData.uid == self.gameobject.uid)
            )

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.occupation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_role": self.job_role.definition_id,
            "business": self.business.uid,
            "start_date": str(self.start_date),
        }

    def __str__(self) -> str:
        return (
            f"Occupation(business={self.business}, "
            f"start_date={self.start_date}, "
            f"role_id={self.job_role.definition_id!r})"
        )

    def __repr__(self) -> str:
        return (
            f"Occupation(business={self.business}, "
            f"start_date={self.start_date}, "
            f"role_id={self.job_role.definition_id!r})"
        )


class BusinessStatus(enum.Enum):
    """The various statuses that a business can be in."""

    OPEN = enum.auto()
    CLOSED = enum.auto()
    PENDING = enum.auto()


class BusinessData(GameData):
    """SQL queryable data about a business."""

    __tablename__ = "businesses"

    uid: Mapped[int] = mapped_column(
        ForeignKey("gameobjects.uid"), primary_key=True, unique=True
    )
    name: Mapped[str]
    owner_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("gameobjects.uid"), nullable=True
    )
    district_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    status: Mapped[BusinessStatus] = mapped_column(default=BusinessStatus.PENDING)


class JobOpeningData(GameData):
    """Information about a job role opening at a business."""

    __tablename__ = "job_openings"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[str]
    business_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    count: Mapped[int]


class Business(Component):
    """A business where characters work."""

    __slots__ = (
        "data",
        "_owner_role",
        "_employee_roles",
        "_district",
        "_owner",
        "_employees",
    )

    data: BusinessData
    """SQl-queryable data about the business."""
    _owner_role: JobRole
    """The role of the business' owner."""
    _employee_roles: dict[str, JobOpeningData]
    """The roles of employees."""
    _district: Optional[GameObject]
    """The district the residence is in."""
    _owner: Optional[GameObject]
    """Owner and their job role ID."""
    _employees: dict[GameObject, JobRole]
    """Employees mapped to their job role ID."""

    def __init__(
        self,
        gameobject: GameObject,
        name: str,
        owner_role: JobRole,
        employee_roles: dict[str, JobOpeningData],
    ) -> None:
        super().__init__(gameobject)
        self.data = BusinessData(
            uid=gameobject.uid,
            name=name,
            owner_id=None,
            district_id=-1,
            status=BusinessStatus.PENDING,
        )
        self._district = None
        self._owner_role = owner_role
        self._employee_roles = employee_roles
        self._owner = None
        self._employees = {}
        gameobject.name = name

    @property
    def district(self) -> Optional[GameObject]:
        """The district the residence is in."""
        return self._district

    @district.setter
    def district(self, value: Optional[GameObject]) -> None:
        """Set the district property."""
        self._district = value
        self.data.district_id = value.uid if value else -1

        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

        if value:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.business.district!{value.uid}"
            )
        else:
            self.gameobject.world.rp_db.delete(
                f"{self.gameobject.uid}.business.district"
            )

    @property
    def name(self) -> str:
        """The name of the business."""
        return self.data.name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the business."""
        with self.gameobject.world.session.begin() as session:
            self.data.name = value
            session.add(self.data)

        self.gameobject.name = value

        if self.data.name:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.business.name!{self.data.name}"
            )
        else:
            self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.business.name")

    @property
    def owner(self) -> Optional[GameObject]:
        """Owner and their job role ID."""
        return self._owner

    @property
    def owner_role(self) -> JobRole:
        """The role of the business' owner."""
        return self._owner_role

    @property
    def employees(self) -> Mapping[GameObject, JobRole]:
        """Employees mapped to their job role ID."""
        return self._employees

    @property
    def status(self) -> BusinessStatus:
        """The current status of the business."""
        return self.data.status

    @status.setter
    def status(self, value: BusinessStatus) -> None:
        """Set the current business status."""
        with self.gameobject.world.session.begin() as session:
            self.data.status = value
            session.add(self.data)

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.business.status!{self.data.status.name}"
        )

    def add_employee(self, employee: GameObject, role: JobRole) -> None:
        """Add an employee to the business.

        Parameters
        ----------
        employee
            The employee to add.
        role
            The employee's job role.
        """
        if self._owner is not None and employee == self._owner:
            raise ValueError("Business owner cannot be added as an employee.")

        if employee in self._employees:
            raise ValueError("Character cannot hold two roles at the same business.")

        if role.definition_id not in self._employee_roles:
            raise ValueError(f"Business does not have employee role with ID: {role}.")

        remaining_slots = self._employee_roles[role.definition_id].count

        if remaining_slots == 0:
            raise ValueError(f"No remaining slots job role with ID: {role}.")

        self._employee_roles[role.definition_id].count -= 1

        self._employees[employee] = role

        with self.gameobject.world.session.begin() as session:
            session.add(self._employee_roles[role.definition_id])

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.business.employees.{employee.uid}"
        )

    def remove_employee(self, employee: GameObject) -> None:
        """Remove an employee from the business.

        Parameters
        ----------
        employee
            The employee to remove.
        """
        if employee not in self._employees:
            raise ValueError(f"{employee.name} is not an employee of this business.")

        role = self._employees[employee]

        del self._employees[employee]

        self._employee_roles[role.definition_id].count += 1

        with self.gameobject.world.session.begin() as session:
            session.add(self._employee_roles[role.definition_id])

        self.gameobject.world.rp_db.delete(
            f"{self.gameobject.uid}.business.employees.{employee.uid}"
        )

    def set_owner(self, owner: Optional[GameObject]) -> None:
        """Set the owner of the business.

        Parameters
        ----------
        owner
            The owner of the business.
        """
        self._owner = owner

        with self.gameobject.world.session.begin() as session:
            self.data.owner_id = owner.uid if owner else None
            session.add(self.data)

        if owner:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.business.owner.{owner.uid}"
            )
        else:
            self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.business.owner")

    def get_open_positions(self) -> Iterable[str]:
        """Get positions at the business with at least one open slot."""
        return [
            job_opening_data.role_id
            for job_opening_data in self._employee_roles.values()
            if job_opening_data.count > 0
        ]

    def on_add(self) -> None:

        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

    def on_remove(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.delete(self.data)

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.business")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "employees": [employee.uid for employee, _ in self._employees.items()],
            "owner": self._owner.uid if self._owner else -1,
            "district": self._district.uid if self._district else -1,
        }


class UnemployedData(GameData):
    """SQL Queryable data about an unemployed character."""

    __tablename__ = "unemployed"

    uid: Mapped[int] = mapped_column(
        ForeignKey("gameobjects.uid"), primary_key=True, unique=True
    )
    timestamp: Mapped[str]


class Unemployed(Component):
    """Tags a character as needing a job, but not having a job."""

    __slots__ = ("_timestamp",)

    _timestamp: SimDate
    """The date the character became unemployed."""

    def __init__(self, gameobject: GameObject, timestamp: SimDate) -> None:
        super().__init__(gameobject)
        self._timestamp = timestamp

    @property
    def timestamp(self) -> SimDate:
        """The date the character became unemployed"""
        return self._timestamp

    def on_add(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.add(
                UnemployedData(
                    uid=self.gameobject.uid, timestamp=self.timestamp.to_iso_str()
                )
            )

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.unemployed.timestamp!{self.timestamp}"
        )

    def on_remove(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.execute(
                delete(UnemployedData).where(UnemployedData.uid == self.gameobject.uid)
            )

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.unemployed")

    def to_dict(self) -> dict[str, Any]:
        return {"timestamp": str(self.timestamp)}


class JobRole:
    """Information about a specific type of job in the world."""

    __slots__ = (
        "name",
        "description",
        "job_level",
        "requirements",
        "effects",
        "recurring_effects",
        "definition_id",
    )

    name: str
    """The name of the role."""
    description: str
    """A description of the role."""
    job_level: int
    """General level of prestige associated with this role."""
    requirements: list[Precondition]
    """Requirement functions for the role."""
    effects: list[Effect]
    """Effects applied when the taking on the role."""
    recurring_effects: list[Effect]
    """Effects applied every month the character has the role."""
    definition_id: str
    """The ID of this job role."""

    def __init__(
        self,
        name: str,
        description: str,
        job_level: int,
        requirements: list[Precondition],
        effects: list[Effect],
        recurring_effects: list[Effect],
        definition_id: str,
    ) -> None:
        self.name = name
        self.description = description
        self.job_level = job_level
        self.requirements = requirements
        self.effects = effects
        self.recurring_effects = recurring_effects
        self.definition_id = definition_id

    def check_requirements(self, gameobject: GameObject) -> bool:
        """Check if a character passes all the requirements for this job."""
        return all([req.check(gameobject)] for req in self.requirements)
