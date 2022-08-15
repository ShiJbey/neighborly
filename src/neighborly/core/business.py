from __future__ import annotations

import functools
import logging
import math
from dataclasses import dataclass
from enum import Enum, IntFlag
from typing import Any, ClassVar, Dict, List, Optional, Protocol, Tuple

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent
from neighborly.core.residence import Resident
from neighborly.core.routine import RoutineEntry, RoutinePriority
from neighborly.core.time import SimDateTime

logger = logging.getLogger(__name__)


class IOccupationPreconditionFn(Protocol):
    """
    A function that must evaluate to True for a character to
    be eligible to hold the occupation.

    Notes
    -----
    This was implemented using a Protocol because the
    implementation of Callable from the typing module
    does not have proper support for **kwargs
    """

    def __call__(self, world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        """
        A function that must evaluate to True for a character to
        be eligible to hold the occupation.

        Arguments
        ---------
        world: World
            The simulation's world instance
        gameobject: GameObject
            The GameObject to evaluate for the position

        Returns
        -------
        bool: True if the character is eligible for the occupation
            False otherwise
        """
        raise NotImplementedError()


def join_preconditions(
    *preconditions: IOccupationPreconditionFn,
) -> IOccupationPreconditionFn:
    """Join multiple occupation precondition functions into a single function"""

    def wrapper(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        return all([p(world, gameobject, **kwargs) for p in preconditions])

    return wrapper


def or_preconditions(
    *preconditions: IOccupationPreconditionFn,
) -> IOccupationPreconditionFn:
    """Only one of the given preconditions has to pass to return True"""

    def wrapper(world: World, gameobject: GameObject, **kwargs: Any) -> bool:
        for p in preconditions:
            if p(world, gameobject, **kwargs):
                return True
        return False

    return wrapper


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
    precondition: Optional[IOccupationPreconditionFn] = None

    def fill_role(self, world: World, business: Business) -> Optional[Occupation]:
        """
        Attempt to find a component character that meets the preconditions
        for this occupation
        """
        candidate_list: List[GameObject] = list(
            filter(
                lambda g: self.precondition(world, g) if self.precondition else True,
                map(
                    lambda res: world.get_gameobject(res[0]),
                    world.get_components(GameCharacter, Resident),
                ),
            )
        )

        if any(candidate_list):
            chosen_candidate = world.get_resource(NeighborlyEngine).rng.choice(
                candidate_list
            )
            occupation = Occupation(self, business.id)
            chosen_candidate.add_component(occupation)
            return occupation
        return None


class OccupationTypeLibrary:
    """Stores OccupationType instances mapped to strings for lookup at runtime"""

    _registry: ClassVar[Dict[str, OccupationType]] = {}

    @classmethod
    def add(
        cls,
        occupation_type: OccupationType,
        name: str = None,
        overwrite_ok: bool = False,
    ) -> None:
        entry_key = name if name else occupation_type.name
        # if entry_key in cls._registry and not overwrite_ok:
        #     logger.warning(f"Attempted to overwrite OcuppationType: ({entry_key})")
        #     return
        cls._registry[entry_key] = occupation_type

    @classmethod
    def get(cls, name: str) -> OccupationType:
        return cls._registry[name]


class Occupation(Component):
    """
    Employment Information about a character
    """

    __slots__ = "_occupation_def", "_years_held", "_business"

    _definition_registry: Dict[str, OccupationType] = {}

    def __init__(
        self,
        occupation_type: OccupationType,
        business: int,
    ) -> None:
        super().__init__()
        self._occupation_def: OccupationType = occupation_type
        self._business: int = business
        self._years_held: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "occupation_def": self._occupation_def.name,
            "business": self._business,
            "years_held": self.get_years_held(),
        }

    def get_type(self) -> OccupationType:
        return self._occupation_def

    def get_business(self) -> int:
        return self._business

    def get_years_held(self) -> int:
        return math.floor(self._years_held)

    def increment_years_held(self, years: float) -> None:
        self._years_held += years

    @classmethod
    def create(cls, world, business: int = -1, **kwargs) -> Occupation:
        type_name = kwargs["name"]
        level = kwargs.get("level", 1)
        preconditions = kwargs.get("preconditions", [])
        return Occupation(
            cls.get_occupation_definition(type_name, level, preconditions),
            business=business,
        )

    @classmethod
    def get_occupation_definition(
        cls, name: str, level: int, precondition: IOccupationPreconditionFn
    ) -> OccupationType:
        if name not in cls._definition_registry:
            cls._definition_registry[name] = OccupationType(
                name=name, level=level, precondition=precondition
            )
        return cls._definition_registry[name]

    def on_remove(self) -> None:
        """Run when the component is removed from the GameObject"""
        world = self.gameobject.world
        workplace = world.get_gameobject(self._business).get_component(Business)
        if workplace.owner != self.gameobject.id:
            workplace.remove_employee(self.gameobject.id)
        else:
            workplace.owner = None

    def on_archive(self) -> None:
        self.gameobject.remove_component(type(self))


@dataclass
class WorkHistoryEntry:
    """Record of a job held by a character"""

    occupation_type: str
    business: int
    start_date: SimDateTime
    end_date: SimDateTime
    reason_for_leaving: Optional[LifeEvent] = None

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


class WorkHistory(Component):
    """
    Stores information about all the jobs that a character
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

    def add_entry(
        self,
        occupation_type: str,
        business: int,
        start_date: SimDateTime,
        end_date: SimDateTime,
        reason_for_leaving: Optional[LifeEvent] = None,
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

    def has_experience_as_a(self, occupation_type: str) -> bool:
        """Return True if the work history has an entry for a given occupation type"""
        return occupation_type in self._categorical_history

    def total_experience_as_a(self, occupation_type: str) -> int:
        """Return the total years of experience someone has as a given occupation type"""
        return functools.reduce(
            lambda _sum, _entry: _sum + _entry.years_held,
            self._categorical_history.get(occupation_type, []),
            0,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "history": [entry.to_dict() for entry in self._chronological_history],
        }

    def __len__(self) -> int:
        return len(self._chronological_history)


class BusinessService(IntFlag):
    NONE = 0
    DRINKING = 1 << 0
    BANKING = 1 << 1
    COLLEGE_EDUCATION = 1 << 2
    CONSTRUCTION = 1 << 3
    COSMETICS = 1 << 4
    CLOTHING = 1 << 5
    FIRE_EMERGENCY = 1 << 6
    FOOD = 1 << 7
    HARDWARE = 1 << 8
    HOME_IMPROVEMENT = 1 << 9
    HOUSING = 1 << 10
    LEGAL = 1 << 11
    MEDICAL_EMERGENCY = 1 << 12
    MORTICIAN = 1 << 13
    RECREATION = 1 << 14
    PUBLIC_SERVICE = 1 << 15
    PRIMARY_EDUCATION = 1 << 16
    REALTY = 1 << 17
    SECONDARY_EDUCATION = 1 << 18
    SHOPPING = 1 << 19
    SOCIALIZING = 1 << 20
    ERRANDS = 1 << 21


class BusinessStatus(Enum):
    PendingOpening = 0
    OpenForBusiness = 1
    ClosedForBusiness = 2


class Business(Component):
    __slots__ = (
        "business_type",
        "name",
        "_years_in_business",
        "operating_hours",
        "_employees",
        "_open_positions",
        "owner",
        "owner_type",
        "status",
        "services",
    )

    def __init__(
        self,
        business_type: str,
        name: str,
        owner_type: str = None,
        owner: int = None,
        open_positions: Dict[str, int] = None,
        operating_hours: Dict[str, List[RoutineEntry]] = None,
        services: BusinessService = BusinessService.NONE,
    ) -> None:
        super().__init__()
        self.business_type: str = business_type
        self.owner_type: Optional[str] = owner_type
        self.name: str = name
        # self._operating_hours: Dict[str, List[RoutineEntry]] = self._create_routines(
        #     parse_schedule_str(business_def.hours)
        # )
        self.operating_hours: Dict[str, List[RoutineEntry]] = (
            operating_hours if operating_hours else {}
        )
        self._open_positions: Dict[str, int] = open_positions if open_positions else {}
        self._employees: Dict[int, str] = {}
        self.owner: Optional[int] = owner
        self.status: BusinessStatus = BusinessStatus.PendingOpening
        self._years_in_business: float = 0.0
        self.services: BusinessService = services

    @property
    def years_in_business(self) -> int:
        return math.floor(self._years_in_business)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_type": self.business_type,
            "name": self.name,
            "operating_hours": self.operating_hours,
            "open_positions": self.operating_hours,
            "employees": self.get_employees(),
            "owner": self.owner if self.owner is not None else -1,
        }

    def needs_owner(self) -> bool:
        return self.owner is None and self.owner_type is not None

    def get_open_positions(self) -> List[str]:
        return [title for title, n in self._open_positions.items() if n > 0]

    def get_employees(self) -> List[int]:
        """Return a list of IDs for current employees"""
        return list(self._employees.keys())

    def add_employee(self, character: int, position: str) -> None:
        """Add character to employees and remove a vacant position"""
        self._employees[character] = position
        self._open_positions[position] -= 1

    def remove_employee(self, character: int) -> None:
        """Remove a character as an employee and add a vacant position"""
        position = self._employees[character]
        del self._employees[character]
        self._open_positions[position] += 1

    def set_business_status(self, status: BusinessStatus) -> None:
        self.status = status

    def increment_years_in_business(self, years: float) -> None:
        self._years_in_business += years

    def __repr__(self) -> str:
        """Return printable representation"""
        return "Business(type='{}', name='{}', owner={}, employees={}, openings={})".format(
            self.business_type,
            self.name,
            self.owner,
            self._employees,
            self._open_positions,
        )

    @classmethod
    def create(cls, world: World, **kwargs) -> Business:
        engine = world.get_resource(NeighborlyEngine)

        business_type: str = kwargs["business_type"]
        business_name: str = engine.name_generator.get_name(
            kwargs.get("name_format", business_type)
        )
        owner_type: Optional[str] = kwargs.get("owner_type")
        employee_types: Dict[str, int] = kwargs.get("employee_types", {})
        services: BusinessService = kwargs.get("services", BusinessService.NONE)
        operating_hours: Dict[str, List[RoutineEntry]] = to_operating_hours(
            kwargs.get("hours", [])
        )

        return Business(
            business_type=business_type,
            name=business_name,
            open_positions=employee_types,
            services=services,
            owner_type=owner_type,
            operating_hours=operating_hours,
        )

    @staticmethod
    def _create_routines(
        times: Dict[str, Tuple[int, int]]
    ) -> Dict[str, List[RoutineEntry]]:
        """Create routine entries given tuples of time intervals mapped to days of the week"""
        schedules: Dict[str, list[RoutineEntry]] = {}

        for day, (opens, closes) in times.items():
            routine_entries: List[RoutineEntry] = []

            if opens > closes:
                # Night shift business have their schedules
                # split between two entries
                routine_entries.append(
                    RoutineEntry(
                        start=opens,
                        end=24,
                        activity="working",
                        location="work",
                        priority=RoutinePriority.HIGH,
                    )
                )

                routine_entries.append(
                    RoutineEntry(
                        start=0,
                        end=closes,
                        activity="working",
                        location="work",
                        priority=RoutinePriority.HIGH,
                    )
                )
            elif opens < closes:
                # Day shift business
                routine_entries.append(
                    RoutineEntry(
                        start=opens,
                        end=closes,
                        activity="working",
                        location="work",
                        priority=RoutinePriority.HIGH,
                    )
                )
            else:
                raise ValueError("Opening and closing times must be different")

            schedules[day] = routine_entries

        return schedules


def to_operating_hours(str_hours: List[str]) -> Dict[str, List[RoutineEntry]]:
    """
    Convert a list of string with times of day and convert
    them to a list of RoutineEntries for when employees
    should report to work and when a business is open to the
    public.

    Parameters
    ----------
    str_hours: List[str]
        The times of day that this business is open

    Returns
    -------
    List[RoutineEntry]
        Routine entries for when this business is operational
    """
    times_to_intervals = {
        "morning": (5, 12),
        "late-morning": (11, 12),
        "early-morning": (5, 8),
        "day": (8, 11),
        "afternoon": (12, 17),
        "evening": (17, 21),
        "night": (21, 23),
    }

    operating_hours: Dict[str, List[RoutineEntry]] = {
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": [],
    }

    routines: List[RoutineEntry] = []

    for time_of_day in str_hours:
        try:
            start, end = times_to_intervals[time_of_day]
            routines.append(RoutineEntry(start, end, location="work", activity="work"))
        except KeyError:
            raise ValueError(f"{time_of_day} is not a valid time of day.")

    for key in operating_hours:
        operating_hours[key].extend(routines)

    return operating_hours
