from __future__ import annotations

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
    Set,
    Tuple,
    Union,
)

from neighborly.core.ecs import Component, GameObject, ISerializable
from neighborly.core.relationship import RelationshipStatus
from neighborly.core.status import StatusComponent
from neighborly.core.time import SimDateTime, Weekday


class Occupation(Component, ISerializable):
    """Information about a character's employment status."""

    __slots__ = "_occupation_type", "_start_date", "_business"

    _occupation_type: str
    """The name of the occupation."""

    _business: int
    """The GameObjectID of the business they work for."""

    _start_date: SimDateTime
    """The date they started this occupation."""

    def __init__(
        self, occupation_type: str, business: int, start_date: SimDateTime
    ) -> None:
        """
        Parameters
        ----------
        occupation_type
            The name of the occupation.
        business
            The business that the character is work for.
        start_date
            The date they started this occupation.
        """
        super().__init__()
        self._occupation_type = occupation_type
        self._business = business
        self._start_date = start_date.copy()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "occupation_type": self._occupation_type,
            "business": self._business,
            "start_date": str(self._start_date),
        }

    @property
    def business(self) -> int:
        """The GameObject ID of the business they work for."""
        return self._business

    @property
    def start_date(self) -> SimDateTime:
        """The date they started the job."""
        return self._start_date

    @property
    def occupation_type(self) -> str:
        """The name of the occupation."""
        return self._occupation_type

    def __repr__(self) -> str:
        return "Occupation(occupation_type={}, business={}, start_date={})".format(
            self.occupation_type, self.business, self.start_date
        )


@dataclass(frozen=True)
class WorkHistoryEntry:
    """A record of a previous occupation."""

    occupation_type: str
    """The name of the job held."""

    business: int
    """The GameObjectID ID of the business the character worked at."""

    years_held: float = 0
    """The number of years the character held this job."""

    reason_for_leaving: str = ""
    """Name of the event that caused the character to leave this job."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "occupation_type": self.occupation_type,
            "business": self.business,
            "years_held": self.years_held,
            "reason_for_leaving": self.reason_for_leaving,
        }


class WorkHistory(Component, ISerializable):
    """Stores records of all previously held occupations."""

    __slots__ = "_history"

    _history: List[WorkHistoryEntry]
    """A collection of previous occupations."""

    def __init__(self) -> None:
        super().__init__()
        self._history = []

    @property
    def entries(self) -> List[WorkHistoryEntry]:
        """All entries in the history."""
        return self._history

    def add_entry(
        self,
        occupation_type: str,
        business: int,
        years_held: float,
        reason_for_leaving: str = "",
    ) -> None:
        """Add an entry to the work history.

        Parameters
        ----------
        occupation_type
            The name of the job held.
        business
            The GameObject ID of the business the character worked at.
        years_held
            The number of years the character held this job.
        reason_for_leaving
            Name of the event that caused the character to leave this job.
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

    _services: Set[str]
    """Service names."""

    def __init__(self, services: Optional[Iterable[str]] = None) -> None:
        """
        Parameters
        ----------
        services
            A starting set of service names.
        """
        super().__init__()
        self._services = set()

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


class ClosedForBusiness(StatusComponent):
    """Tags a business as closed and no longer active in the simulation."""

    is_persistent = True


class OpenForBusiness(StatusComponent):
    """Tags a business as actively conducting business in the simulation."""

    pass


class OperatingHours(Component, ISerializable):
    """Defines when a business is open and closed."""

    __slots__ = "_hours"

    _hours: Dict[Weekday, Tuple[int, int]]
    """Weekdays mapped to hour intervals."""

    def __init__(self, hours: Dict[Weekday, Tuple[int, int]]) -> None:
        """
        Parameters
        ----------
        hours
            Days of the week mapped to hour intervals that the business is open.
        """
        super().__init__()
        self._hours = hours

    @property
    def operating_hours(self) -> Dict[Weekday, Tuple[int, int]]:
        """The operating hours for the business."""
        return self.operating_hours

    def to_dict(self) -> Dict[str, Any]:
        return {"hours": self._hours}


class Business(Component, ISerializable):
    """Businesses are places where characters are employed."""

    __slots__ = ("_owner_type", "_employees", "_open_positions", "_owner")

    _owner_type: str
    """The name of the occupation that the business owner has."""

    _open_positions: Dict[str, int]
    """The names of occupations mapped to the number of open positions."""

    _employees: Dict[int, str]
    """The GameObject IDs of employees mapped to their occupation's name."""

    _owner: Optional[int]
    """The GameObjectID of the owner of this business."""

    def __init__(
        self,
        owner_type: str,
        employee_types: Dict[str, int],
    ) -> None:
        """
        Parameters
        ----------
        owner_type
            The name of the OccupationType for the GameObject
            that owns this business.
        employee_types
            The names of OccupationTypes mapped to the total number
            of that occupation that can work at an instance of this
            business.
        """
        super().__init__()
        self._owner_type = owner_type
        self._open_positions = employee_types
        self._employees = {}
        self._owner = None

    @property
    def owner(self) -> Optional[int]:
        """The GameObject ID of the owner of the business."""
        return self._owner

    @property
    def owner_type(self) -> str:
        """The name of the occupation type of the business' owner."""
        return self._owner_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner_type": self.owner_type,
            "open_positions": self._open_positions,
            "employees": [
                {"title": title, "uid": uid} for uid, title in self._employees.items()
            ],
            "owner": {
                "title": self.owner_type,
                "uid": self.owner if self.owner is not None else -1,
            },
        }

    def needs_owner(self) -> bool:
        """Check if the business need an owner.

        Returns
        -------
        bool
            True if the business is missing an owner. False otherwise.
        """
        return self.owner is None

    def get_open_positions(self) -> List[str]:
        """Get all the open job titles.

        Returns
        -------
        List[str]
            All the names of all open positions at the business.
        """
        return [title for title, count in self._open_positions.items() if count > 0]

    def get_employees(self) -> List[int]:
        """Get all current employees.

        Returns
        -------
        List[int]
            Returns the GameObject IDs of all employees of this business.
        """
        return list(self._employees.keys())

    def set_owner(self, owner: Optional[int]) -> None:
        """Set the ID for the owner of the business.

        Parameters
        ----------
        owner
            The GameObject ID of the new business owner.
        """
        self._owner = owner

    def add_employee(self, employee: int, position: str) -> None:
        """Add employee and remove a vacant position.

        Parameters
        ----------
        character
            The GameObject ID of the employee.
        position
            The name of the employee's position.
        """
        self._employees[employee] = position
        self._open_positions[position] -= 1

    def remove_employee(self, employee: int) -> None:
        """Remove an employee and vacate their position.

        Parameters
        ----------
        employee
            The GameObject ID of an employee.
        """
        position = self._employees[employee]
        del self._employees[employee]
        self._open_positions[position] += 1

    def __repr__(self) -> str:
        return "{}(owner={}, employees={}, openings={})".format(
            self.__class__.__name__,
            self.owner,
            self._employees,
            self._open_positions,
        )


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


class OccupationType:
    """Shared information about all occupations with this type."""

    __slots__ = "name", "level", "rules"

    name: str
    """Name of the position."""

    level: int
    """Prestige or socioeconomic status associated with the position."""

    rules: List[Tuple[Precondition, ...]]
    """
    Function that determines of a candidate gameobject meets th requirements
    of the occupation. Preconditions are lists of lists where each sublist is
    a single rule and all callable in that list need to return true for the
    rule to pass. Only one rule needs to return True for a GameObject to qualify
    for the occupation type.
    """

    def __init__(
        self,
        name: str,
        level: int = 1,
        rules: Optional[
            Union[
                Precondition,
                Tuple[Precondition, ...],
                List[Tuple[Precondition, ...]],
            ]
        ] = None,
    ) -> None:
        self.name: str = name
        self.level: int = level
        self.rules: List[Tuple[Precondition, ...]] = []

        if rules:
            if isinstance(rules, list):
                self.rules = rules
            elif isinstance(rules, tuple):
                self.rules.append(rules)
            else:
                self.rules.append((rules,))

    def add_precondition(self, rule: Union[Tuple[Precondition], Precondition]) -> None:
        """Add a new precondition rule to the occupation"""
        if isinstance(rule, tuple):
            self.rules.append(rule)
        else:
            self.rules.append((rule,))

    def passes_preconditions(self, gameobject: GameObject) -> bool:
        """Check if a GameObject passes any of the preconditions"""
        if len(self.rules) == 0:
            return True

        for rule in self.rules:
            satisfies_rule: bool = True

            # All clauses (functions) within a rule (sub-list) need
            # to return True for the rule to be satisfied
            for clause in rule:
                if clause(gameobject) is False:
                    satisfies_rule = False
                    break

            # Only one rule needs to be satisfied for the gameobject
            # to pass the preconditions.
            if satisfies_rule:
                return True

        return False


class BusinessOwner(StatusComponent):
    """Tags a GameObject as being the owner of a business."""

    __slots__ = "business"

    business: int
    """The GameObject ID of the business owned."""

    def __init__(self, business: int) -> None:
        """
        Parameters
        ----------
        business
            The GameObject ID of the business owned.
        """
        super().__init__()
        self.business: int = business

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "business": self.business}


class Unemployed(StatusComponent):
    """Tags a character as being able to work but lacking a job."""

    pass


class InTheWorkforce(StatusComponent):
    """Tags a character as being eligible to work."""

    pass


class BossOf(RelationshipStatus):
    """Tags the owner of a relationship as being the employer of the target."""

    pass


class EmployeeOf(RelationshipStatus):
    """Tags the owner of a relationship as being the employee of the target."""

    pass


class CoworkerOf(RelationshipStatus):
    """Tags the owner of a relationship as being a coworker of the target."""

    pass


class OccupationTypes:
    """A collection of OccupationType information for lookup at runtime."""

    _registry: ClassVar[Dict[str, OccupationType]] = {}
    """Occupation names mapped to definition data."""

    @classmethod
    def add(
        cls,
        occupation_type: OccupationType,
    ) -> None:
        """Add a new occupation type to the library.

        Parameters
        ----------
        occupation_type
            The occupation type instance to add.
        """
        cls._registry[occupation_type.name] = occupation_type

    @classmethod
    def get(cls, name: str) -> OccupationType:
        """Get an OccupationType by name.

        Parameters
        ----------
        name
            The registered name of the OccupationType

        Returns
        -------
        OccupationType
        """
        return cls._registry[name]
