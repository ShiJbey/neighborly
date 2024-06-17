"""Business Components.

This module contains class definitions for components and classes that model businesses
in the settlement and character occupations.

"""

from __future__ import annotations

import enum
from typing import Any, Iterable, Optional

from neighborly.datetime import SimDate
from neighborly.ecs import Component, GameObject
from neighborly.effects.base_types import Effect
from neighborly.preconditions.base_types import Precondition


class Occupation(Component):
    """Information about a character's employment status."""

    __slots__ = ("start_date", "business", "job_role")

    job_role: JobRole
    """The job role."""
    business: GameObject
    """The business they work for."""
    start_date: SimDate
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
        self.job_role = job_role
        self.business = business
        self.start_date = start_date

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


class Business(Component):
    """A business where characters work."""

    __slots__ = (
        "name",
        "owner_role",
        "employee_roles",
        "owner",
        "employees",
        "status",
    )

    name: str
    """The name of the business."""
    owner_role: JobRole
    """The role of the business' owner."""
    employee_roles: dict[JobRole, int]
    """The roles of employees."""
    owner: Optional[GameObject]
    """Owner and their job role ID."""
    employees: dict[GameObject, JobRole]
    """Employees mapped to their job role ID."""
    status: BusinessStatus
    """Current status of the business."""

    def __init__(
        self,
        name: str,
        owner_role: JobRole,
        employee_roles: dict[JobRole, int],
    ) -> None:
        super().__init__()
        self.name = name
        self.owner_role = owner_role
        self.employee_roles = employee_roles
        self.owner = None
        self.employees = {}
        self.status = BusinessStatus.CLOSED

    def get_open_positions(self) -> Iterable[str]:
        """Get positions at the business with at least one open slot."""
        return [
            role.definition_id
            for role, count in self.employee_roles.items()
            if count > 0
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "employees": [employee.uid for employee, _ in self.employees.items()],
            "owner": self.owner.uid if self.owner else -1,
        }


class Unemployed(Component):
    """Tags a character as needing a job, but not having a job."""

    __slots__ = ("timestamp",)

    timestamp: SimDate
    """The date the character became unemployed."""

    def __init__(self, timestamp: SimDate) -> None:
        super().__init__()
        self.timestamp = timestamp

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
    definition_id: str
    """The ID of this job role."""

    def __init__(
        self,
        name: str,
        description: str,
        job_level: int,
        requirements: list[Precondition],
        effects: list[Effect],
        definition_id: str,
    ) -> None:
        self.name = name
        self.description = description
        self.job_level = job_level
        self.requirements = requirements
        self.effects = effects
        self.definition_id = definition_id

    def check_requirements(self, gameobject: GameObject) -> bool:
        """Check if a character passes all the requirements for this job."""
        return all(req.check(gameobject) for req in self.requirements)
