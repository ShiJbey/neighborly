import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, ClassVar, Callable

from neighborly.core import name_generation as name_gen
from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec


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


class Occupation:
    """
    Employment Information about a character
    """
    __slots__ = "_occupation_type", "_years_held", "_business"

    def __init__(
            self,
            occupation_type: OccupationType,
            business: int,
    ) -> None:
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


def hours_str_to_arr(hours_str: str) -> List[bool]:
    """Converts a time interval to boolean array of length 24"""
    # Split the string
    opens, closes = tuple(
        map(
            lambda time_str: int(time_str.strip().split(":")[0]),
            hours_str.strip().split("-")
        )
    )

    hours = [False] * 24

    if opens > closes:
        # Night shift business
        for i in range(closes, 24):
            hours[i] = True
        for i in range(0, opens):
            hours[i] = True
    elif opens < closes:
        # Day shift business
        for i in range(opens, closes):
            hours[i] = True
    else:
        raise ValueError("Opening and closing times must be different")

    return hours


def hours_str_to_schedule(hours_str: str) -> Dict[str, List[bool]]:
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

    schedule: Dict[str, List[bool]] = {}

    for schedule_tup in schedule_sets:
        if len(schedule_tup) == 1:
            days = "MTWRFSU"
            hours = schedule_tup[0]
        else:
            days, hours = schedule_tup

        hour_arr = hours_str_to_arr(hours)
        for abbrev in days:
            day = abbrev_to_day[abbrev]
            if day in schedule:
                raise RuntimeError(
                    f"Day ({day}) listed twice in operating hours")
            else:
                schedule[day] = hour_arr

    return schedule


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
        self._operating_hours: Dict[str, List[bool]] = \
            hours_str_to_schedule(business_type.hours)
        self._open_positions: Dict[str, int] = business_type.employees
        self._employees: List[Tuple[str, int]] = []
        self._owner: Optional[int] = owner

    def get_type(self) -> BusinessType:
        return self._business_type

    def get_name(self) -> str:
        return self._name

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


class BusinessFactory(AbstractFactory):
    """Create instances of the default business component"""

    def __init__(self) -> None:
        super().__init__("Business")

    def create(self, spec: ComponentSpec) -> Business:
        name = name_gen.get_name(spec["name"])

        conf = BusinessType(
            name=spec["business type"],
            name_pattern=spec["name pattern"],
            hours=spec["hours"],
            employees=spec.get_attributes().get("employees", {}),
            owner=spec.get_attributes().get("owner", None),
            max_instances=spec.get_attributes().get("max instances", 9999),
            min_population=spec.get_attributes().get("min population", 0),
        )

        return Business(conf, name)
