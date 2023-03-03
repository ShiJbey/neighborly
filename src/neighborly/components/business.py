from __future__ import annotations

import logging
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, Union

from neighborly.core.ecs import Component
from neighborly.core.ecs.ecs import GameObject
from neighborly.core.relationship import RelationshipStatus
from neighborly.core.status import StatusComponent
from neighborly.core.time import Weekday

logger = logging.getLogger(__name__)


class Occupation(Component):
    """Information about a character's employment status"""

    __slots__ = "_occupation_type", "_years_held", "_business"

    def __init__(
        self, occupation_type: str, business: int, years_held: float = 0.0
    ) -> None:
        """
        Parameters
        ----------
        occupation_type: str
            The name of the occupation
        business: int
            The business that the character is work for
        years_held: float, optional
            The number of years the character has held this job
            (defaults to 0.0)
        """

        super().__init__()
        self._occupation_type: str = occupation_type
        self._business: int = business
        self._years_held: float = years_held

    def to_dict(self) -> Dict[str, Any]:
        """Return serialized dict representation of an Occupation component"""
        return {
            "occupation_type": self._occupation_type,
            "business": self._business,
            "years_held": self._years_held,
        }

    @property
    def business(self) -> int:
        """Get the business the character works for"""
        return self._business

    @property
    def years_held(self) -> float:
        """Get the number of years this character has worked this job"""
        return self._years_held

    @property
    def occupation_type(self) -> str:
        """Get the type of occupation this is"""
        return self._occupation_type

    def set_years_held(self, years: float) -> None:
        """Set the number of years this character has held this job"""
        self._years_held = years

    def __repr__(self) -> str:
        return "Occupation(occupation_type={}, business={}, years_held={})".format(
            self.occupation_type, self.business, self.years_held
        )


@dataclass(frozen=True)
class WorkHistoryEntry:
    """
    Record of a job held by a character

    Attributes
    ----------
    occupation_type: str
        The name of the job held
    business: int
        The unique ID of the business the character worked at
    years_held: float
        The number of years the character held this job
    reason_for_leaving: Optional[str]
        Name of the event that caused the character to leave this job
    """

    occupation_type: str
    business: int
    years_held: float = 0
    reason_for_leaving: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation for serialization"""

        return {
            "occupation_type": self.occupation_type,
            "business": self.business,
            "years_held": self.years_held,
            "reason_for_leaving": self.reason_for_leaving,
        }


class WorkHistory(Component):
    """Stores information about all the jobs that a character has held"""

    __slots__ = "_chronological_history", "_categorical_history"

    def __init__(self) -> None:
        super().__init__()
        self._chronological_history: List[WorkHistoryEntry] = []
        self._categorical_history: Dict[str, List[WorkHistoryEntry]] = {}

    @property
    def entries(self) -> List[WorkHistoryEntry]:
        """Get all WorkHistoryEntries"""
        return self._chronological_history

    def add_entry(
        self,
        occupation_type: str,
        business: int,
        years_held: float,
        reason_for_leaving: str = "",
    ) -> None:
        """
        Add an entry to the work history

        Parameters
        ----------
        occupation_type: str
            The name of the job held
        business: int
            The unique ID of the business the character worked at
        years_held: float
            The number of years the character held this job
        reason_for_leaving: str, optional
            Name of the event that caused the character to leave this job
        """
        entry = WorkHistoryEntry(
            occupation_type=occupation_type,
            business=business,
            years_held=years_held,
            reason_for_leaving=reason_for_leaving,
        )

        self._chronological_history.append(entry)

        if occupation_type not in self._categorical_history:
            self._categorical_history[occupation_type] = []

        self._categorical_history[occupation_type].append(entry)

    def get_last_entry(self) -> Optional[WorkHistoryEntry]:
        """Get the latest entry to WorkHistory"""
        if self._chronological_history:
            return self._chronological_history[-1]
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history": [entry.to_dict() for entry in self._chronological_history],
        }

    def __len__(self) -> int:
        return len(self._chronological_history)

    def __repr__(self) -> str:
        return "WorkHistory({})".format(
            [e.__repr__() for e in self._chronological_history]
        )


@dataclass(frozen=True)
class Service:
    """A service offered by a business establishment

    Attributes
    ----------
    uid: int
        The unique ID for this service type (unique only among other service types)
    name: str
        The name of the service offered

    Notes
    -----
    DO NOT INSTANTIATE THIS CLASS DIRECTLY. ServiceType instances are created
    as needed by the ServiceLibrary class
    """

    uid: int
    name: str

    def __hash__(self) -> int:
        return self.uid

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Service):
            return self.uid == other.uid
        raise TypeError(f"Expected ServiceType but was {type(object)}")


class Services(Component):
    """
    Tracks the services offered by a business

    Attributes
    ----------
    services: Set[Service]
        The set of services offered by the business
    """

    __slots__ = "services"

    def __init__(self, services: Set[Service]) -> None:
        super().__init__()
        self.services: Set[Service] = services

    def has_service(self, service: Service) -> bool:
        """
        Check if a business offers a service

        Parameters
        ----------
        service: Service
            The service to check for

        Returns
        -------
        bool
            Returns True of the business offers this service
        """
        return service in self.services

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self.services)

    def to_dict(self) -> Dict[str, Any]:
        return {"services": [str(s) for s in self.services]}


class ClosedForBusiness(StatusComponent):
    is_persistent = True


class OpenForBusiness(StatusComponent):
    __slots__ = "duration"

    def __init__(self) -> None:
        super().__init__()
        self.duration: float = 0.0


class IBusinessType(Component, ABC):
    """Empty interface for creating types of businesses like Restaurants, ETC"""

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"BusinessType({self.__class__.__name__})"

    def to_dict(self) -> Dict[str, Any]:
        return {}


class OperatingHours(Component):
    """Defines when a business is open and closed"""

    __slots__ = "_hours"

    def __init__(self, hours: Dict[Weekday, Tuple[int, int]]) -> None:
        """
        Parameters
        ----------
        hours: Optional[Dict[Weekday, Tuple[int, int]]]
            Days of the week mapped to hour intervals that the business
            is open
        """
        super().__init__()
        self._hours: Dict[Weekday, Tuple[int, int]] = hours

    @property
    def operating_hours(self) -> Dict[Weekday, Tuple[int, int]]:
        return self.operating_hours

    def to_dict(self) -> Dict[str, Any]:
        return {"hours": self._hours}


class Business(Component):
    """Businesses are owned by and employ characters in the simulation"""

    __slots__ = ("_owner_type", "_employees", "_open_positions", "_owner")

    def __init__(
        self,
        owner_type: str,
        employee_types: Dict[str, int],
    ) -> None:
        """
        Parameters
        ----------
        owner_type: str
            The name of the OccupationType for the GameObject
            that owns this business
        employee_types: Optional[Dict[str, int]]
            The names of OccupationTypes mapped to the total number
            of that occupation that can work at an instance of this
            business
        """
        super().__init__()
        self._owner_type: str = owner_type
        self._open_positions: Dict[str, int] = employee_types
        self._employees: Dict[int, str] = {}
        self._owner: Optional[int] = None

    @property
    def owner(self) -> Optional[int]:
        return self._owner

    @property
    def owner_type(self) -> str:
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
        """Returns True if this business needs to hire an owner"""
        return self.owner is None

    def get_open_positions(self) -> List[str]:
        """Returns all the open job titles"""
        return sum(
            [[title] * count for title, count in self._open_positions.items()], []
        )

    def get_employees(self) -> List[int]:
        """Return a list of IDs for current employees"""
        return list(self._employees.keys())

    def set_owner(self, owner: Optional[int]) -> None:
        """Set the ID for the owner of the business"""
        self._owner = owner

    def add_employee(self, character: int, position: str) -> None:
        """Add entity to employees and remove a vacant position"""
        self._employees[character] = position
        self._open_positions[position] -= 1

    def remove_employee(self, character: int) -> None:
        """Remove an entity as an employee and add a vacant position"""
        position = self._employees[character]
        del self._employees[character]
        self._open_positions[position] += 1

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(owner={}, employees={}, openings={})".format(
            self.__class__.__name__,
            self.owner,
            self._employees,
            self._open_positions,
        )


class Precondition(Protocol):
    def __call__(self, gameobject: GameObject) -> bool:
        raise NotImplementedError


class OccupationType:
    """
    Shared information about all occupations with this type

    Attributes
    ----------
    name: str
        Name of the position
    level: int
        Prestige or socioeconomic status associated with the position
    rules: List[List[Callable[[GameObject], bool]]]
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

    def add_precondition(self, rule: Union[List[Precondition], Precondition]) -> None:
        """Add a new precondition rule to the occupation"""
        if isinstance(rule, list):
            self.rules.append(rule)
        else:
            self.rules.append([rule])

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
    """Marks a character as owning a business"""

    def __init__(self, business: int) -> None:
        super().__init__()
        self.business: int = business

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "business": self.business}


class Unemployed(StatusComponent):
    """Marks a character as being able to work but lacking a job"""

    pass


class InTheWorkforce(StatusComponent):
    """Tags a character as being eligible to work"""

    pass


class BossOf(RelationshipStatus):
    pass


class EmployeeOf(RelationshipStatus):
    pass


class CoworkerOf(RelationshipStatus):
    pass
