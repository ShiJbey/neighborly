"""Business Components.

This module contains class definitions for components and classes that model businesses
in the settlement and character occupations.

"""

from __future__ import annotations

import enum
from typing import Any, Iterable, Mapping, Optional

from neighborly.datetime import SimDate
from neighborly.ecs import Component, GameObject
from neighborly.effects.base_types import Effect
from neighborly.preconditions.base_types import Precondition


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
        super().__init__()
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


class Business(Component):
    """A business where characters work."""

    __slots__ = (
        "_name",
        "_owner_role",
        "_employee_roles",
        "_district",
        "_owner",
        "_employees",
        "_status",
    )

    _name: str
    """The name of the business."""
    _owner_role: JobRole
    """The role of the business' owner."""
    _employee_roles: dict[JobRole, int]
    """The roles of employees."""
    _district: Optional[GameObject]
    """The district the residence is in."""
    _owner: Optional[GameObject]
    """Owner and their job role ID."""
    _employees: dict[GameObject, JobRole]
    """Employees mapped to their job role ID."""
    _status: BusinessStatus
    """Current status of the business."""

    def __init__(
        self,
        name: str,
        owner_role: JobRole,
        employee_roles: dict[JobRole, int],
    ) -> None:
        super().__init__()
        self._district = None
        self._name = name
        self._owner_role = owner_role
        self._employee_roles = employee_roles
        self._owner = None
        self._employees = {}
        self._status = BusinessStatus.CLOSED

    @property
    def district(self) -> Optional[GameObject]:
        """The district the residence is in."""
        return self._district

    @district.setter
    def district(self, value: Optional[GameObject]) -> None:
        """Set the district property."""
        self._district = value

    @property
    def name(self) -> str:
        """The name of the business."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the business."""
        self._name = value
        self.gameobject.name = value

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
        return self._status

    @status.setter
    def status(self, value: BusinessStatus) -> None:
        """Set the current business status."""
        self._status = value

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

        if role not in self._employee_roles:
            raise ValueError(f"Business does not have employee role with ID: {role}.")

        remaining_slots = self._employee_roles[role]

        if remaining_slots == 0:
            raise ValueError(f"No remaining slots job role with ID: {role}.")

        self._employee_roles[role] -= 1

        self._employees[employee] = role

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

        self._employee_roles[role] += 1

    def set_owner(self, owner: Optional[GameObject]) -> None:
        """Set the owner of the business.

        Parameters
        ----------
        owner
            The owner of the business.
        """
        self._owner = owner

    def get_open_positions(self) -> Iterable[str]:
        """Get positions at the business with at least one open slot."""
        return [
            role.definition_id
            for role, count in self._employee_roles.items()
            if count > 0
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "employees": [employee.uid for employee, _ in self._employees.items()],
            "owner": self._owner.uid if self._owner else -1,
            "district": self._district.uid if self._district else -1,
        }


class Unemployed(Component):
    """Tags a character as needing a job, but not having a job."""

    __slots__ = ("_timestamp",)

    _timestamp: SimDate
    """The date the character became unemployed."""

    def __init__(self, timestamp: SimDate) -> None:
        super().__init__()
        self._timestamp = timestamp

    @property
    def timestamp(self) -> SimDate:
        """The date the character became unemployed"""
        return self._timestamp

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
        return all([req.check({"target": gameobject})] for req in self.requirements)
