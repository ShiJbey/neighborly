from __future__ import annotations

import logging
import math
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from neighborly.components.routine import RoutineEntry, RoutinePriority
from neighborly.core import query
from neighborly.core.ecs import Component
from neighborly.core.event import Event
from neighborly.core.time import SimDateTime, Weekday

logger = logging.getLogger(__name__)


class Occupation(Component):
    """
    Employment Information about an entity
    """

    __slots__ = "_occupation_type", "_years_held", "_business", "_level", "_start_date"

    def __init__(
        self,
        occupation_type: str,
        business: int,
        level: int,
        start_date: SimDateTime,
    ) -> None:
        super().__init__()
        self._occupation_type: str = occupation_type
        self._business: int = business
        self._level: int = level
        self._years_held: float = 0.0
        self._start_date: SimDateTime = start_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "occupation_type": self._occupation_type,
            "level": self._level,
            "business": self._business,
            "years_held": self._years_held,
        }

    @property
    def business(self) -> int:
        return self._business

    @property
    def years_held(self) -> int:
        return math.floor(self._years_held)

    @property
    def level(self) -> int:
        return self._level

    @property
    def occupation_type(self) -> str:
        return self._occupation_type

    @property
    def start_date(self) -> SimDateTime:
        return self._start_date

    def increment_years_held(self, years: float) -> None:
        self._years_held += years

    def __repr__(self) -> str:
        return "Occupation(occupation_type={}, business={}, level={}, years_held={})".format(
            self.occupation_type, self.business, self.level, self.years_held
        )


@dataclass
class WorkHistoryEntry:
    """Record of a job held by an entity"""

    occupation_type: str
    business: int
    start_date: SimDateTime
    end_date: SimDateTime
    reason_for_leaving: Optional[Event] = None

    @property
    def years_held(self) -> int:
        return (self.start_date - self.end_date).years

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation for serialization"""

        ret = {
            "occupation_type": self.occupation_type,
            "business": self.business,
            "start_date": self.start_date.to_iso_str(),
            "end_date": self.end_date.to_iso_str(),
        }

        if self.reason_for_leaving:
            # This should probably point to a unique ID for the
            # event, but we will leave it as the name of the event for now
            ret["reason_for_leaving"] = self.reason_for_leaving.name

        return ret

    def __repr__(self) -> str:
        return (
            "WorkHistoryEntry(type={}, business={}, start_date={}, end_date={})".format(
                self.occupation_type,
                self.business,
                self.start_date.to_iso_str(),
                self.end_date.to_iso_str() if self.end_date else "N/A",
            )
        )


class WorkHistory(Component):
    """
    Stores information about all the jobs that an entity
    has held

    Attributes
    ----------
    _chronological_history: List[WorkHistoryEntry]
        List of previous job in order from oldest to most recent
    """

    __slots__ = "_chronological_history", "_categorical_history"

    def __init__(self) -> None:
        super(Component, self).__init__()
        self._chronological_history: List[WorkHistoryEntry] = []
        self._categorical_history: Dict[str, List[WorkHistoryEntry]] = {}

    @property
    def entries(self) -> List[WorkHistoryEntry]:
        return self._chronological_history

    def add_entry(
        self,
        occupation_type: str,
        business: int,
        start_date: SimDateTime,
        end_date: SimDateTime,
        reason_for_leaving: Optional[Event] = None,
    ) -> None:
        """Add an entry to the work history"""
        entry = WorkHistoryEntry(
            occupation_type=occupation_type,
            business=business,
            start_date=start_date,
            end_date=end_date,
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
            **super().to_dict(),
            "history": [entry.to_dict() for entry in self._chronological_history],
        }

    def __len__(self) -> int:
        return len(self._chronological_history)

    def __repr__(self) -> str:
        return "WorkHistory({})".format(
            [e.__repr__() for e in self._chronological_history]
        )


class ServiceType:
    """A service that can be offered by a business establishment"""

    __slots__ = "_uid", "_name"

    def __init__(self, uid: int, name: str) -> None:
        self._uid = uid
        self._name = name

    @property
    def uid(self) -> int:
        return self._uid

    @property
    def name(self) -> str:
        return self._name

    def __hash__(self) -> int:
        return self._uid

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ServiceType):
            return self.uid == other.uid
        raise TypeError(f"Expected ServiceType but was {type(object)}")


class ServiceTypes:
    """
    Repository of various services offered
    """

    _next_id: int = 1
    _name_to_service: Dict[str, ServiceType] = {}
    _id_to_name: Dict[int, str] = {}

    @classmethod
    def __contains__(cls, service_name: str) -> bool:
        """Return True if a service type exists with the given name"""
        return service_name.lower() in cls._name_to_service

    @classmethod
    def get(cls, service_name: str) -> ServiceType:
        lc_service_name = service_name.lower()

        if lc_service_name in cls._name_to_service:
            return cls._name_to_service[lc_service_name]

        uid = cls._next_id
        cls._next_id = cls._next_id + 1
        service_type = ServiceType(uid, lc_service_name)
        cls._name_to_service[lc_service_name] = service_type
        cls._id_to_name[uid] = lc_service_name
        return service_type


class Services(Component):
    __slots__ = "_services"

    def __init__(self, services: Set[ServiceType]) -> None:
        super().__init__()
        self._services: Set[ServiceType] = services

    def __contains__(self, service_name: str) -> bool:
        return ServiceTypes.get(service_name) in self._services

    def has_service(self, service: ServiceType) -> bool:
        return service in self._services


class ClosedForBusiness(Component):
    pass


class OpenForBusiness(Component):
    __slots__ = "duration"

    def __init__(self) -> None:
        super().__init__()
        self.duration: float = 0.0


class IBusinessType(Component, ABC):
    """Empty interface for creating types of businesses like Restaurants, ETC"""

    pass


class Business(Component):
    __slots__ = (
        "name",
        "operating_hours",
        "_employees",
        "_open_positions",
        "owner",
        "owner_type",
    )

    def __init__(
        self,
        name: str,
        owner_type: Optional[str] = None,
        owner: Optional[int] = None,
        open_positions: Optional[Dict[str, int]] = None,
        operating_hours: Optional[Dict[Weekday, Tuple[int, int]]] = None,
    ) -> None:
        super().__init__()
        self.name: str = name
        self.owner_type: Optional[str] = owner_type
        self.operating_hours: Dict[Weekday, Tuple[int, int]] = (
            operating_hours if operating_hours else {}
        )
        self._open_positions: Dict[str, int] = open_positions if open_positions else {}
        if owner_type is not None:
            if owner_type in self._open_positions:
                self._open_positions[owner_type] += 1
            else:
                self._open_positions[owner_type] = 0
        self._employees: Dict[int, str] = {}
        self.owner: Optional[int] = owner

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "name": self.name,
            "operating_hours": self.operating_hours,
            "open_positions": self._open_positions,
            "employees": self.get_employees(),
            "owner": self.owner if self.owner is not None else -1,
            "owner_type": self.owner_type if self.owner_type is not None else "",
        }

    def needs_owner(self) -> bool:
        return self.owner is None and self.owner_type is not None

    def get_open_positions(self) -> List[str]:
        return [title for title, n in self._open_positions.items() if n > 0]

    def get_employees(self) -> List[int]:
        """Return a list of IDs for current employees"""
        return list(self._employees.keys())

    def set_owner(self, owner: Optional[int]) -> None:
        """Set the ID for the owner of the business"""
        self.owner = owner

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
        return "Business(name={}, owner={}, employees={}, openings={})".format(
            self.name,
            self.owner,
            self._employees,
            self._open_positions,
        )

    def create_routines(self) -> Dict[Weekday, RoutineEntry]:
        """Create routine entries given tuples of time intervals mapped to days of the week"""
        routine_entries: Dict[Weekday, RoutineEntry] = {}

        for day, (opens, closes) in self.operating_hours.items():
            routine_entries[day] = RoutineEntry(
                start=opens,
                end=closes,
                location=self.gameobject.id,
                priority=RoutinePriority.HIGH,
                tags=["work"],
            )

        return routine_entries


class InTheWorkforce(Component):
    """Tags a character as being eligible to work"""

    pass


@dataclass
class OccupationType:
    """
    Shared information about all occupations with this type

    Attributes
    ----------
    name: str
        Name of the position
    level: int
        Prestige or socioeconomic status associated with the position
    precondition: Optional[IOccupationPreconditionFn]
        Function that determines of a candidate gameobject meets th requirements
        of the occupation
    """

    name: str
    level: int = 1
    description: str = ""
    precondition: Optional[query.QueryFilterFn] = None

    def __repr__(self) -> str:
        return f"OccupationType(name={self.name}, level={self.level})"
