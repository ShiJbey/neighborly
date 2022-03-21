import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, ClassVar, Callable

from neighborly.core import name_generation as name_gen
from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec
from neighborly.core.routine import RoutineEntry, RoutinePriority


class OccupationType:
    """
    Shared information about all occupations with this type

    Attributes
    ----------
    _name: str
        Name of the position
    _level: int
        Prestige or socioeconomic status associated with the position
    _preconditions: List[Callable[..., bool]]
        Preconditions functions that need to pass for a character
        to qualify for this occupation type

    Class Attributes
    ----------------
    _type_registry: Dict[str, OccupationType]
        Registered instances of OccupationTypes
    _precondition_registry: Dict[str, Callable[..., bool]]
        Registered preconditions used to determine
        if a character qualifies for a position
    """

    __slots__ = "_name", "_level", "_preconditions"

    _type_registry: Dict[str, 'OccupationType'] = {}
    _precondition_registry: Dict[str, Callable[..., bool]] = {}

    def __init__(
            self,
            name: str,
            level: int,
            preconditions: Optional[List[Callable[..., bool]]] = None
    ) -> None:
        self._name: str = name
        self._level: int = level
        self._preconditions: List[Callable[..., bool]] = \
            preconditions if preconditions else []

    def get_name(self) -> str:
        return self._name

    def get_level(self) -> int:
        return self._level

    def get_preconditions(self) -> List[Callable[..., bool]]:
        return self._preconditions

    @classmethod
    def register_type(cls, occupation_type: 'OccupationType') -> None:
        cls._type_registry[occupation_type._name] = occupation_type

    @classmethod
    def get_registered_type(cls, name: str) -> 'OccupationType':
        return cls._type_registry[name]

    @classmethod
    def register_precondition(cls, precondition: Callable[..., bool]) -> None:
        cls._precondition_registry[precondition.__name__] = precondition

    def __repr__(self) -> str:
        return "{}(name={}, level={}, preconditions=[{}])".format(
            self.__class__.__name__,
            self._name,
            self._level,
            [fn.__name__ for fn in self._preconditions]
        )


class Occupation(Component):
    """
    Employment Information about a character
    """
    __slots__ = "_occupation_type", "_years_held", "_business"

    def __init__(
            self,
            occupation_type: OccupationType,
            business: int,
    ) -> None:
        super().__init__()
        self._occupation_type: OccupationType = occupation_type
        self._business: int = business
        self._years_held: float = 0.0

    def get_type(self) -> OccupationType:
        return self._occupation_type

    def get_business(self) -> int:
        return self._business

    def get_years_held(self) -> int:
        return math.floor(self._years_held)

    def increment_years_held(self, years: float) -> None:
        self._years_held += years


@dataclass
class BusinessType:
    """
    Shared information about all businesses that
    have this type
    """
    _type_registry: ClassVar[Dict[str, 'BusinessType']] = {}

    name: str
    name_pattern: str
    hours: str
    owner: Optional[str] = None
    max_instances: int = 9999
    instances: int = 0
    min_population: int = 0
    employees: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def register_type(cls, business_type: 'BusinessType') -> None:
        """Register one or more business types for later use"""
        cls._type_registry[business_type.name] = business_type

    @classmethod
    def get_registered_type(cls, name: str) -> 'BusinessType':
        return cls._type_registry[name]

    @classmethod
    def get_all_types(cls) -> List['BusinessType']:
        return list(cls._type_registry.values())


class Business(Component):
    __slots__ = "_business_type", "_name", "_years_in_business", \
                "_operating_hours", "_employees", "_open_positions", "_owner"

    def __init__(
            self,
            business_type: BusinessType,
            name: str,
            owner: Optional[int] = None
    ) -> None:
        super().__init__()
        self._business_type: BusinessType = business_type
        self._name: str = name
        self._operating_hours: Dict[str, List[RoutineEntry]] = \
            self.hours_str_to_schedule(business_type.hours)
        self._open_positions: Dict[str, int] = business_type.employees
        self._employees: List[Tuple[str, int]] = []
        self._owner: Optional[int] = owner

    def needs_owner(self) -> bool:
        return self._owner is None and self.get_type().owner is not None

    def get_open_positions(self) -> List[str]:
        return [title for title, n in self._open_positions if n > 0]

    def get_type(self) -> BusinessType:
        return self._business_type

    def get_name(self) -> str:
        return self._name

    def hire_owner(self, character: int) -> None:
        self._owner = character

    def on_start(self) -> None:
        self.gameobject.set_name(str(self._name))

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(type='{}', name='{}', owner={}, employees={}, openings={})".format(
            self.__class__.__name__,
            self._business_type.name,
            self._name,
            self._owner,
            self._employees,
            self._open_positions
        )

    @staticmethod
    def hours_str_to_schedule(hours_str: str) -> Dict[str, List[RoutineEntry]]:
        """Convert an operating hours string to dict of days with hours"""
        # Split the operating hours by commas
        schedule_sets = \
            list(map(
                lambda s: tuple(
                    map(lambda x: x.strip(), s.strip().split(' '))),
                hours_str.split(",")
            ))

        abbrev_to_day = {
            "M": "Monday", "T": "Tuesday",
            "W": "Wednesday", "R": "Thursday",
            "F": "Friday", "S": "Saturday",
            "U": "Sunday"
        }

        schedule: Dict[str, List[RoutineEntry]] = {}

        for schedule_tup in schedule_sets:
            if len(schedule_tup) == 1:
                days = "MTWRFSU"
                hours = schedule_tup[0]
            else:
                days, hours = schedule_tup

            opens, closes = tuple(
                map(
                    lambda time_str: int(time_str.strip().split(":")[0]),
                    hours.strip().split("-")
                )
            )

            routine_entries: List[RoutineEntry] = []

            if opens > closes:
                # Night shift business have their schedules
                # split between two entries
                routine_entries.append(RoutineEntry(
                    start=opens,
                    end=24,
                    activity='working',
                    location='work',
                    priority=RoutinePriority.HIGH,
                ))

                routine_entries.append(RoutineEntry(
                    start=0,
                    end=closes,
                    activity='working',
                    location='work',
                    priority=RoutinePriority.HIGH,
                ))
            elif opens < closes:
                # Day shift business
                routine_entries.append(RoutineEntry(
                    start=opens,
                    end=closes,
                    activity='working',
                    location='work',
                    priority=RoutinePriority.HIGH,
                ))
            else:
                raise ValueError("Opening and closing times must be different")

            for abbrev in days:
                day = abbrev_to_day[abbrev]
                if day in schedule:
                    raise RuntimeError(
                        f"Day ({day}) listed twice in operating hours")
                else:
                    schedule[day] = routine_entries

        return schedule


class BusinessFactory(AbstractFactory):
    """Create instances of the default business component"""

    def __init__(self) -> None:
        super().__init__("Business")

    def create(self, spec: ComponentSpec) -> Business:
        type_name: Optional[str] = spec.get_attribute("business_type")

        if type_name is None:
            raise TypeError("Expected to fund business_type str but was None")

        business_type = BusinessType.get_registered_type(type_name)

        name = name_gen.get_name(business_type.name_pattern)

        return Business(business_type, name)
