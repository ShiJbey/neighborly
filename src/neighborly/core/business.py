from __future__ import annotations

import logging
import math
import re
from abc import ABC
from dataclasses import dataclass, field
from random import Random
from typing import Any, Dict, List, Optional, Set, Tuple

from neighborly.builtin.components import Active
from neighborly.core import query
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World, component_info
from neighborly.core.event import Event
from neighborly.core.routine import RoutineEntry, RoutinePriority, time_str_to_int
from neighborly.core.time import SimDateTime, Weekday

logger = logging.getLogger(__name__)


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
    precondition: Optional[query.QueryFilterFn] = field(default=lambda w, *g: True)

    def fill_role(
        self,
        world: World,
        business: Business,
        rng: Random,
        candidate: Optional[GameObject] = None,
    ) -> Optional[Tuple[GameObject, Occupation]]:
        """
        Attempt to find a component entity that meets the preconditions
        for this occupation
        """
        q = query.Query(
            find=("Candidate",),
            clauses=[
                query.where(
                    query.has_components(GameCharacter, Unemployed, Active), ""
                ),
                query.filter_(self.precondition),
            ],
        )

        if candidate:
            candidate_list = q.execute(world, Candidate=candidate.id)
        else:
            candidate_list = q.execute(world)

        if candidate_list:
            chosen_candidate = world.get_gameobject(rng.choice(candidate_list)[0])
            return chosen_candidate, Occupation(
                occupation_type=self.name,
                business=business.gameobject.id,
                level=self.level,
                start_date=world.get_resource(SimDateTime).copy(),
            )

        return None

    def __repr__(self) -> str:
        return f"OccupationType(name={self.name}, level={self.level})"


class OccupationTypes:
    """Collection OccupationType information for lookup at runtime"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, OccupationType] = {}

    def add(
        self,
        occupation_type: OccupationType,
        name: Optional[str] = None,
    ) -> None:
        entry_key = name if name else occupation_type.name
        if entry_key in self._registry:
            logger.debug(f"Overwriting OccupationType: ({entry_key})")
        self._registry[entry_key] = occupation_type

    def get(self, name: str) -> OccupationType:
        """
        Get an OccupationType by name

        Parameters
        ----------
        name: str
            The registered name of the OccupationType

        Returns
        -------
        OccupationType

        Raises
        ------
        KeyError
            When there is not an OccupationType
            registered to that name
        """
        return self._registry[name]


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
        super().__init__()
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

    def __eq__(self, other: ServiceType) -> bool:
        return self.uid == other.uid


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


class Services(Component):

    __slots__ = "_services"

    def __init__(self, services: Set[ServiceType]) -> None:
        super().__init__()
        self._services: Set[ServiceType] = services

    def __contains__(self, service_name: str) -> bool:
        return ServiceTypes.get(service_name) in self._services

    def has_service(self, service: ServiceType) -> bool:
        return service in self._services


@component_info(
    "Closed For Business",
    "This business is no longer open and nobody works here.",
)
class ClosedForBusiness(Component):
    pass


@component_info(
    "Open For Business",
    "This business open for business and people can travel here.",
)
class OpenForBusiness(Component):

    __slots__ = "duration"

    def __init__(self) -> None:
        super().__init__()
        self.duration: float = 0.0


@component_info(
    "Pending Opening",
    "This business is built, but has no owner.",
)
class PendingOpening(Component):

    __slots__ = "duration"

    def __init__(self) -> None:
        super().__init__()
        self.duration: float = 0.0


class IBusinessType(Component, ABC):
    """Empty interface for creating types of businesses like Restaurants, ETC"""

    pass


class Business(Component):
    __slots__ = (
        "operating_hours",
        "_employees",
        "_open_positions",
        "owner",
        "owner_type",
    )

    def __init__(
        self,
        owner_type: Optional[str] = None,
        owner: Optional[int] = None,
        open_positions: Optional[Dict[str, int]] = None,
        operating_hours: Optional[Dict[Weekday, Tuple[int, int]]] = None,
    ) -> None:
        super().__init__()
        self.owner_type: Optional[str] = owner_type
        self.operating_hours: Dict[Weekday, Tuple[int, int]] = (
            operating_hours if operating_hours else {}
        )
        self._open_positions: Dict[str, int] = open_positions if open_positions else {}
        self._employees: Dict[int, str] = {}
        self.owner: Optional[int] = owner

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
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
        return "Business(owner={}, employees={}, openings={})".format(
            self.owner,
            self._employees,
            self._open_positions,
        )

    @classmethod
    def create(cls, world: World, **kwargs) -> Business:

        owner_type: Optional[str] = kwargs.get("owner_type")
        employee_types: Dict[str, int] = kwargs.get("employee_types", {})
        operating_hours: Dict[Weekday, Tuple[int, int]] = parse_operating_hour_str(
            kwargs.get("hours", "day")
        )

        return Business(
            open_positions=employee_types,
            owner_type=owner_type,
            operating_hours=operating_hours,
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


@component_info(
    "Unemployed",
    "Character doesn't have a job",
)
class Unemployed(Component):
    __slots__ = "duration_days"

    def __init__(self) -> None:
        super().__init__()
        self.duration_days: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "duration_days": self.duration_days}


@component_info(
    "In the Workforce",
    "This Character is eligible for employment opportunities.",
)
class InTheWorkforce(Component):
    pass


def parse_operating_hour_str(
    operating_hours_str: str,
) -> Dict[Weekday, Tuple[int, int]]:
    """
    Convert a string representing the hours of operation
    for a business to a dictionary representing the days
    of the week mapped to tuple time intervals for when
    the business is open.

    Parameters
    ----------
    operating_hours_str: str
        String indicating the operating hours

    Notes
    -----
    The following a re valid formats for the operating hours string
    (1a interval 24HR) ## - ##
        Opening hour - closing hour
        Assumes that the business is open all days of the week
    (1b interval 12HR AM/PM) ## AM - ## PM
        Twelve-hour time interval
    (2 interval-alias) "morning", "day", "night", or ...
        Single string that maps to a preset time interval
        Assumes that the business is open all days of the week
    (3 days + interval) MTWRFSU: ## - ##
        Specify the time interval and the specific days of the
        week that the business is open
    (4 days + interval-alias) MTWRFSU: "morning", or ...
        Specify the days of the week and a time interval for
        when the business will be open

    Returns
    -------
    Dict[str, Tuple[int, int]]
        Days of the week mapped to lists of time intervals
    """

    interval_aliases = {
        "morning": (5, 12),
        "late-morning": (11, 12),
        "early-morning": (5, 8),
        "day": (8, 11),
        "afternoon": (12, 17),
        "evening": (17, 21),
        "night": (21, 23),
    }

    # time_alias = {
    #     "early-morning": "02:00",
    #     "dawn": "06:00",
    #     "morning": "08:00",
    #     "late-morning": "10:00",
    #     "noon": "12:00",
    #     "afternoon": "14:00",
    #     "evening": "17:00",
    #     "night": "21:00",
    #     "midnight": "23:00",
    # }

    operating_hours_str = operating_hours_str.strip()

    # Check for number interval
    if match := re.fullmatch(
        r"[0-2]?[0-9]\s*(PM|AM)?\s*-\s*[0-2]?[0-9]\s*(PM|AM)?", operating_hours_str
    ):
        interval_strs: List[str] = list(
            map(lambda s: s.strip(), match.group(0).split("-"))
        )

        interval: Tuple[int, int] = (
            time_str_to_int(interval_strs[0]),
            time_str_to_int(interval_strs[1]),
        )

        if 23 < interval[0] < 0:
            raise ValueError(f"Interval start not within bounds [0,23]: {interval}")
        if 23 < interval[1] < 0:
            raise ValueError(f"Interval end not within bounds [0,23]: {interval}")

        return {d: interval for d in list(Weekday)}

    # Check for interval alias
    elif match := re.fullmatch(r"[a-zA-Z]+", operating_hours_str):
        alias = match.group(0)
        if alias in interval_aliases:
            interval = interval_aliases[alias]
            return {d: interval for d in list(Weekday)}
        else:
            raise ValueError(f"Invalid interval alias in: '{operating_hours_str}'")

    # Check for days with number interval
    elif match := re.fullmatch(
        r"[MTWRFSU]+\s*:\s*[0-2]?[0-9]\s*-\s*[0-2]?[0-9]", operating_hours_str
    ):
        days_section, interval_section = tuple(match.group(0).split(":"))
        days_section = days_section.strip()
        interval_strs: List[str] = list(
            map(lambda s: s.strip(), interval_section.strip().split("-"))
        )
        interval: Tuple[int, int] = (int(interval_strs[0]), int(interval_strs[1]))

        if 23 < interval[0] < 0:
            raise ValueError(f"Interval start not within bounds [0,23]: {interval}")
        if 23 < interval[1] < 0:
            raise ValueError(f"Interval end not within bounds [0,23]: {interval}")

        return {Weekday.from_abbr(d): interval for d in days_section.strip()}

    # Check for days with alias interval
    elif match := re.fullmatch(r"[MTWRFSU]+\s*:\s*[a-zA-Z]+", operating_hours_str):
        days_section, alias = tuple(match.group(0).split(":"))
        days_section = days_section.strip()
        alias = alias.strip()
        if alias in interval_aliases:
            interval = interval_aliases[alias]
            return {Weekday.from_abbr(d): interval for d in days_section.strip()}
        else:
            raise ValueError(
                f"Invalid interval alias ({alias}) in: '{operating_hours_str}'"
            )

    raise ValueError(f"Invalid operating hours string: '{operating_hours_str}'")
