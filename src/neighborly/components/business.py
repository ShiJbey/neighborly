"""Components for businesses and business-related relationship statuses.

"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
)

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, GameObject, ISerializable
from neighborly.core.life_event import LifeEvent
from neighborly.core.relationship import IRelationshipStatus
from neighborly.core.status import IStatus


class Occupation(Component, ISerializable, ABC):
    """Information about a character's employment status."""

    __slots__ = "start_year", "business"

    business: GameObject
    """The business they work for."""

    start_year: int
    """The year they started this occupation."""

    social_status: ClassVar[int] = 1
    """The socioeconomic status associated with this occupation."""

    def __init__(self, business: GameObject, start_year: int) -> None:
        """
        Parameters
        ----------
        business
            The business that the character is work for.
        start_year
            The date they started this occupation.
        """
        super().__init__()
        self.business = business
        self.start_year = start_year

    def get_social_status(self) -> int:
        """Get the socioeconomic status associated with this position."""
        return self.social_status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "business": self.business.uid,
            "start_year": str(self.start_year),
            "social_status": self.get_social_status(),
        }

    def __str__(self) -> str:
        return "{}(business={}, start_year={}, social_status={})".format(
            type(self).__name__,
            self.business,
            self.start_year,
            self.get_social_status(),
        )

    def __repr__(self) -> str:
        return "{}(business={}, start_year={}, social_status={})".format(
            type(self).__name__,
            self.business,
            self.start_year,
            self.get_social_status(),
        )


@dataclass(frozen=True)
class WorkHistoryEntry:
    """A record of a previous occupation."""

    occupation_type: Type[Occupation]
    """The occupation type definition."""

    business: GameObject
    """The business the character worked at."""

    years_held: float = 0
    """The number of years the character held the job."""

    reason_for_leaving: Optional[LifeEvent] = None
    """The event that caused the character to leave this job."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "occupation_type": self.occupation_type.__name__,
            "business": self.business.uid,
            "years_held": self.years_held,
            "reason_for_leaving": self.reason_for_leaving.event_id
            if self.reason_for_leaving
            else -1,
        }


class WorkHistory(Component, ISerializable):
    """Stores records of all previously held occupations."""

    __slots__ = "_history"

    _history: List[WorkHistoryEntry]
    """Information about previous occupations."""

    def __init__(self) -> None:
        super().__init__()
        self._history = []

    @property
    def entries(self) -> List[WorkHistoryEntry]:
        """All entries in the history."""
        return self._history

    def add_entry(
        self,
        occupation_type: Type[Occupation],
        business: GameObject,
        years_held: float,
        reason_for_leaving: Optional[LifeEvent] = None,
    ) -> None:
        """Add an entry to the work history.

        Parameters
        ----------
        occupation_type
            The occupation type definition.
        business
            The business that the character worked at.
        years_held
            The number of years the character held the job.
        reason_for_leaving
            The event that caused the character to leave this job.
        """
        entry = WorkHistoryEntry(
            occupation_type=occupation_type,
            business=business,
            years_held=years_held,
            reason_for_leaving=reason_for_leaving,
        )

        self._history.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history": [entry.to_dict() for entry in self._history],
        }

    def __len__(self) -> int:
        return len(self._history)

    def __repr__(self) -> str:
        return "WorkHistory({})".format([e.__repr__() for e in self._history])


class Services(Component, ISerializable):
    """Tracks a set of services offered by a business."""

    __slots__ = "_services"

    _services: OrderedSet[str]
    """Service names."""

    def __init__(self, services: Optional[Iterable[str]] = None) -> None:
        """
        Parameters
        ----------
        services
            A starting set of service names.
        """
        super().__init__()
        self._services = OrderedSet([])

        if services:
            for name in services:
                self.add_service(name)

    def add_service(self, service: str) -> None:
        """Add a service.

        Parameters
        ----------
        service
            The name of a service.
        """
        self._services.add(service.lower())

    def remove_service(self, service: str) -> None:
        """Remove a service.

        Parameters
        ----------
        service:
            The name of a service.
        """
        self._services.remove(service.lower())

    def __iter__(self) -> Iterator[str]:
        return self._services.__iter__()

    def __contains__(self, service: str) -> bool:
        return service.lower() in self._services

    def __str__(self) -> str:
        return ", ".join(self._services)

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._services)

    def to_dict(self) -> Dict[str, Any]:
        return {"services": list(self._services)}


class ClosedForBusiness(IStatus):
    """Tags a business as closed and no longer active in the simulation."""

    is_persistent = True


class OpenForBusiness(IStatus):
    """Tags a business as actively conducting business in the simulation."""

    pass


class Business(Component, ISerializable):
    """Businesses are places where characters are employed."""

    __slots__ = ("_owner_position", "_employees", "_employee_positions", "_owner")

    _owner_position: Type[Occupation]
    """The job position information for the business owner."""

    _employee_positions: Dict[Type[Occupation], int]
    """The positions available to work at this business."""

    _employees: Dict[GameObject, Type[Occupation]]
    """The Employee GameObjects mapped to their occupation roles."""

    _owner: Optional[GameObject]
    """The owner of the business."""

    def __init__(
        self,
        owner_type: Type[Occupation],
        employee_types: Dict[Type[Occupation], int],
    ) -> None:
        """
        Parameters
        ----------
        owner_type
            The OccupationType for the owner of the business.
        employee_types
            OccupationTypes mapped to the total number of that occupation that can work at an instance of this
            business.
        """
        super().__init__()
        self._owner_position = owner_type
        self._employee_positions = employee_types
        self._employees = {}
        self._owner = None

    @property
    def owner_type(self) -> Type[Occupation]:
        """The name of the occupation type of the business' owner."""
        return self._owner_position

    @property
    def owner(self) -> Optional[GameObject]:
        return self._owner

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner_type": self.owner_type.__name__,
            "open_positions": {
                occupation_type.__name__: open_slots
                for occupation_type, open_slots in self._employee_positions.items()
            },
            "employees": [
                {
                    "title": role.__name__,
                    "uid": employee.uid,
                }
                for employee, role in self._employees.items()
            ],
            "owner": {
                "title": self._owner_position.__name__,
                "uid": self._owner.uid if self._owner else -1,
            },
        }

    def set_owner(self, owner: Optional[GameObject]) -> None:
        """Set the owner for the business.

        Parameters
        ----------
        owner
            The owner or non if removing the owner
        """
        self._owner = owner

    def get_open_positions(self) -> List[Type[Occupation]]:
        """Get all the open job positions.

        Returns
        -------
        List[JobPosition]
            All the open positions at the business.
        """
        return [
            position
            for position, open_slots in self._employee_positions.items()
            if open_slots > 0
        ]

    def iter_employees(self) -> Iterator[Tuple[GameObject, Type[Occupation]]]:
        """Get iterator to the collection of current employees."""
        return self._employees.items().__iter__()

    def add_employee(self, employee: GameObject, role: Type[Occupation]) -> None:
        """Add employee and remove a vacant position.

        Parameters
        ----------
        employee
            The GameObject ID of the employee.
        role
            The name of the employee's position.
        """
        self._employees[employee] = role
        self._employee_positions[role] -= 1

    def remove_employee(self, employee: GameObject) -> None:
        """Remove an employee and vacate their position.

        Parameters
        ----------
        employee
            The GameObject representing an employee.
        """
        role = self._employees[employee]
        self._employee_positions[role] += 1
        del self._employees[employee]

    def get_employee_role(self, employee: GameObject) -> Type[Occupation]:
        """Get the occupation role associated with this employee.

        Parameters
        ----------
        employee
            The employee to get the role for

        Returns
        -------
        Type[Occupation]
            Their occupation role
        """
        return self._employees[employee]

    def __repr__(self) -> str:
        return "{}(employees={}, openings={})".format(
            self.__class__.__name__,
            self._employees,
            self._employee_positions,
        )


class BusinessOwner(IStatus):
    """Tags a GameObject as being the owner of a business."""

    __slots__ = "business"

    business: GameObject
    """The business owned."""

    def __init__(self, year_created: int, business: GameObject) -> None:
        """
        Parameters
        ----------
        business
            The business owned.
        """
        super().__init__(year_created)
        self.business: GameObject = business

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "business": self.business.uid}


class Unemployed(IStatus):
    """Tags a character as being able to work but lacking a job."""

    pass


class InTheWorkforce(IStatus):
    """Tags a character as being eligible to work."""

    pass


class BossOf(IRelationshipStatus):
    """Tags the owner of a relationship as being the employer of the target."""

    pass


class EmployeeOf(IRelationshipStatus):
    """Tags the owner of a relationship as being the employee of the target."""

    pass


class CoworkerOf(IRelationshipStatus):
    """Tags the owner of a relationship as being a coworker of the target."""

    pass


class JobRequirementFn(Protocol):
    """A function that returns a precondition rule for characters holding jobs."""

    def __call__(self, gameobject: GameObject, *args: Any) -> bool:
        raise NotImplementedError


class JobRequirementRule:
    __slots__ = "_job_requirement_fn", "_args"

    _job_requirement_fn: JobRequirementFn
    """A function that evaluates is the gameobject passes a precondition."""

    _args: Tuple[Any, ...]
    """Positional arguments passed to the job requirement function."""

    def __init__(self, fn: JobRequirementFn, *args: Any) -> None:
        self._job_requirement_fn = fn
        self._args = args

    def __call__(self, gameobject: GameObject) -> bool:
        return self._job_requirement_fn(gameobject, *self._args)


class Precondition(Protocol):
    """A callable that checks if a GameObjects meets some criteria."""

    def __call__(self, gameobject: GameObject) -> bool:
        """
        Parameters
        ----------
        gameobject
            The gameobject to check the precondition for.

        Returns
        -------
        bool
            True if the GameObject meets the conditions, False otherwise.
        """
        raise NotImplementedError


class JobRequirements:
    """Specifies precondition rules for an occupation type."""

    __slots__ = "_rules"

    _rules: List[Precondition]
    """A collection of preconditions."""

    def __init__(self, rules: Optional[Iterable[Precondition]] = None) -> None:
        super().__init__()
        self._rules = [*rules] if rules else []

    def add_rule(self, rule: Precondition) -> None:
        """Add a new rule to the job requirements"""
        self._rules.append(rule)

    def passes_requirements(self, gameobject: GameObject) -> bool:
        """Check if a GameObject passes any of the requirement rules.

        Parameters
        ----------
        gameobject
            The GameObject to evaluate.

        Returns
        -------
        bool
            True if the gameobject passes at least one precondition.
        """
        if self._rules:
            for rule in self._rules:
                if rule(gameobject):
                    return True
            return False
        else:
            return True


class JobRequirementLibrary:
    """A shared collection of job requirement rule used by occupation type requirement prefabs."""

    __slots__ = "_rules"

    _rules: dict[str, JobRequirements]
    """String identifiers mapped to precondition functions."""

    def __init__(self) -> None:
        self._rules = {}

    def add_requirement(self, occupation_type: str, job_req: Precondition) -> None:
        """Add a new job requirement rule.

        Parameters
        ----------
        occupation_type
            The occupation type to add a requirement to.
        job_req
            The function to add.
        """
        if occupation_type not in self._rules:
            self._rules[occupation_type] = JobRequirements()
        self._rules[occupation_type].add_rule(job_req)

    def get_requirements(self, occupation_type: str) -> JobRequirements:
        """Retrieve a job requirement rule by name.

        Parameters
        ----------
        occupation_type
            The name of a rule.

        Returns
        -------
        JobRequirements
        """
        if occupation_type in self._rules:
            return self._rules[occupation_type]
        return JobRequirements()
