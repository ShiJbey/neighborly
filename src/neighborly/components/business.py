"""Business Components.

This module contains class definitions for components and classes that model businesses
in the settlement and character occupations.

"""

from __future__ import annotations

import enum
from typing import Any, Iterable, Mapping, Optional

from neighborly.datetime import SimDate
from neighborly.defs.base_types import StatModifierData
from neighborly.ecs import Component, GameObject


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
        self, job_role: JobRole, business: GameObject, start_date: SimDate
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
            "job_role": self.job_role.gameobject.uid,
            "business": self.business.uid,
            "start_date": str(self.start_date),
        }

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(business={self.business}, "
            f"start_date={self.start_date}, role_id={self.job_role.display_name})"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(business={self.business}, "
            f"start_date={self.start_date}, role_id={self.job_role.display_name})"
        )


class BusinessStatus(enum.Enum):
    """Current activity status of the business."""

    CLOSED = enum.auto()
    OPEN = enum.auto()
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
        "status",
    )

    _name: str
    """The name of the business."""
    _owner_role: JobRole
    """The role of the business' owner."""
    _employee_roles: dict[JobRole, int]
    """The roles of employees."""
    _district: GameObject
    """The district the residence is in."""
    _owner: Optional[GameObject]
    """Owner and their job role ID."""
    _employees: dict[GameObject, JobRole]
    """Employees mapped to their job role ID."""
    status: BusinessStatus
    """Current activity status of the business."""

    def __init__(
        self,
        district: GameObject,
        name: str,
        owner_role: JobRole,
        employee_roles: dict[JobRole, int],
    ) -> None:
        super().__init__()
        self._district = district
        self._name = name
        self._owner_role = owner_role
        self._employee_roles = employee_roles
        self._owner = None
        self._employees = {}
        self.status = BusinessStatus.PENDING

    @property
    def district(self) -> GameObject:
        """The district the residence is in."""
        return self._district

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

    def get_open_positions(self) -> Iterable[JobRole]:
        """Get positions at the business with at least one open slot."""
        return [
            role_name for role_name, count in self._employee_roles.items() if count > 0
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "employees": [employee.uid for employee, _ in self._employees.items()],
            "owner": self._owner.uid if self._owner else -1,
            "district": self._district.uid,
        }


class JobRole(Component):
    """Information about a specific type of job in the world."""

    __slots__ = (
        "definition_id",
        "display_name",
        "description",
        "job_level",
        "requirements",
        "stat_modifiers",
        "periodic_stat_boosts",
        "periodic_skill_boosts",
    )

    definition_id: str
    """The ID of this job role."""
    display_name: str
    """The name of the role."""
    description: str
    """A description of the role."""
    job_level: int
    """General level of prestige associated with this role."""
    requirements: list[str]
    """Requirement functions for the role."""
    stat_modifiers: list[StatModifierData]
    """Stat modifiers applied when a character takes on this role."""
    periodic_stat_boosts: list[StatModifierData]
    """Periodic boosts repeatedly applied to stats while a character holds the role."""
    periodic_skill_boosts: list[StatModifierData]
    """Periodic boosts repeatedly applied to skills while a character holds the role."""

    def __init__(
        self,
        definition_id: str,
        display_name: str,
        description: str,
        job_level: int,
        requirements: list[str],
        stat_modifiers: list[StatModifierData],
        periodic_stat_boosts: list[StatModifierData],
        periodic_skill_boosts: list[StatModifierData],
    ) -> None:
        super().__init__()
        self.definition_id = definition_id
        self.display_name = display_name
        self.description = description
        self.job_level = job_level
        self.requirements = requirements
        self.stat_modifiers = stat_modifiers
        self.periodic_stat_boosts = periodic_stat_boosts
        self.periodic_skill_boosts = periodic_skill_boosts

    def check_requirements(self, gameobject: GameObject) -> bool:
        """Check if a character passes all the requirements for this job."""
        raise NotImplementedError()

    def to_dict(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name,
            "description": self.description,
            "job_level": self.job_level,
            "definition_id": self.definition_id,
        }
