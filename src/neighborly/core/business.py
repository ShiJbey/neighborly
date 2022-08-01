from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from typing import Any, ClassVar, Dict, List, Optional, Protocol, Tuple

from neighborly.core.ecs import Component, Event, GameObject, IEventListener, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.routine import RoutineEntry, RoutinePriority


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

    def __call__(self, gameobject: GameObject, **kwargs: Any) -> bool:
        """
        A function that must evaluate to True for a character to
        be eligible to hold the occupation.

        Arguments
        ---------
        gameobject: GameObject
            GameObject to evaluate

        Returns
        -------
        bool: True if the character is eligible for the occupation
            False otherwise
        """
        raise NotImplementedError()


@dataclass
class OccupationDefinition:
    """
    Shared information about all occupations with this type

    Attributes
    ----------
    name: str
        Name of the position
    level: int
        Prestige or socioeconomic status associated with the position
    preconditions: List[OccupationPreconditionFn]
        Preconditions functions that need to pass for a character
        to qualify for this occupation type

    Class Attributes
    ----------------
    _type_registry: Dict[str, OccupationType]
        Registered instances of OccupationTypes
    _precondition_registry: Dict[str, OccupationPreconditionFn]
        Registered preconditions used to determine
        if a character qualifies for a position
    """

    _type_registry: ClassVar[Dict[str, OccupationDefinition]] = {}
    _precondition_registry: ClassVar[Dict[str, IOccupationPreconditionFn]] = {}

    name: str
    level: int = 1
    preconditions: List[IOccupationPreconditionFn] = field(default_factory=list)

    @classmethod
    def register_type(cls, occupation_type: OccupationDefinition) -> None:
        cls._type_registry[occupation_type.name] = occupation_type

    @classmethod
    def get_registered_type(cls, name: str) -> OccupationDefinition:
        return cls._type_registry[name]

    @classmethod
    def register_precondition(
        cls, name: str, precondition: IOccupationPreconditionFn
    ) -> None:
        cls._precondition_registry[name] = precondition


class Occupation(Component, IEventListener):
    """
    Employment Information about a character
    """

    __slots__ = "_occupation_def", "_years_held", "_business"

    _definition_registry: Dict[str, OccupationDefinition] = {}

    def __init__(
        self,
        occupation_type: OccupationDefinition,
        business: int,
    ) -> None:
        super().__init__()
        self._occupation_def: OccupationDefinition = occupation_type
        self._business: int = business
        self._years_held: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "occupation_def": self._occupation_def.name,
            "business": self._business,
            "years_held": self.get_years_held(),
        }

    def get_type(self) -> OccupationDefinition:
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
        cls, name: str, level: int, preconditions: List[IOccupationPreconditionFn]
    ) -> OccupationDefinition:
        if name not in cls._definition_registry:
            cls._definition_registry[name] = OccupationDefinition(
                name=name, level=level, preconditions=preconditions
            )
        return cls._definition_registry[name]

    def will_handle_event(self, event: Event) -> bool:
        return True

    def handle_event(self, event: Event) -> bool:
        event_type = event.get_type()
        if event_type == "death":
            print("Character died and now we remove them from their job.")
            # Remove the character from their work position
            self.gameobject.remove_component(Occupation)
        return True

    def on_remove(self) -> None:
        """Run when the component is removed from the GameObject"""
        world = self.gameobject.world
        workplace = world.get_gameobject(self._business).get_component(Business)
        if workplace.get_owner() != self.gameobject.id:
            workplace.remove_employee(self.gameobject.id)


class BusinessServiceFlag(Flag):
    NONE = 0
    ALCOHOL = auto()
    BANKING = auto()
    COLLEGE_EDUCATION = auto()
    CONSTRUCTION = auto()
    COSMETICS = auto()
    CLOTHING = auto()
    FIRE_EMERGENCY = auto()
    FOOD = auto()
    HARDWARE = auto()
    HOME_IMPROVEMENT = auto()
    HOUSING = auto()
    LEGAL = auto()
    MEDICAL_EMERGENCY = auto()
    MORTICIAN = auto()
    RECREATION = auto()
    PUBLIC_SERVICE = auto()
    PRIMARY_EDUCATION = auto()
    REALTY = auto()
    SECONDARY_EDUCATION = auto()
    SHOPPING = auto()
    SOCIALIZING = auto()


@dataclass
class BusinessDefinition:
    """
    Shared information about all businesses that
    have this type
    """

    _type_registry: ClassVar[Dict[str, "BusinessDefinition"]] = {}

    name: str
    hours: str
    name_pattern: Optional[str] = None
    owner_type: str = ""
    max_instances: int = 9999
    instances: int = 0
    min_population: int = 0
    employees: Dict[str, int] = field(default_factory=dict)
    services: List[str] = field(default_factory=list)
    service_flags: BusinessServiceFlag = field(init=False)

    def __post_init__(self) -> None:
        self.service_flags = BusinessServiceFlag.NONE
        for service_name in self.services:
            self.service_flags |= BusinessServiceFlag[
                service_name.strip().upper().replace(" ", "_")
            ]

    @classmethod
    def register_type(cls, business_type: "BusinessDefinition") -> None:
        """Register one or more business types for later use"""
        cls._type_registry[business_type.name] = business_type

    @classmethod
    def get_registered_type(cls, name: str) -> "BusinessDefinition":
        return cls._type_registry[name]

    @classmethod
    def get_all_types(cls) -> List["BusinessDefinition"]:
        return list(cls._type_registry.values())


class BusinessStatus(Enum):
    PendingOpening = 0
    OpenForBusiness = 1
    ClosedForBusiness = 2


class Business(Component):
    __slots__ = (
        "business_def",
        "_name",
        "_years_in_business",
        "_operating_hours",
        "_employees",
        "_open_positions",
        "_owner",
        "_status",
    )

    def __init__(
        self, business_def: BusinessDefinition, name: str, owner: Optional[int] = None
    ) -> None:
        super().__init__()
        self.business_def: BusinessDefinition = business_def
        self._name: str = name
        # self._operating_hours: Dict[str, List[RoutineEntry]] = self._create_routines(
        #     parse_schedule_str(business_def.hours)
        # )
        self._operating_hours: Dict[str, List[RoutineEntry]] = {}
        self._open_positions: Dict[str, int] = {**business_def.employees}
        self._employees: Dict[int, str] = {}
        self._owner: Optional[int] = owner
        self._status: BusinessStatus = BusinessStatus.PendingOpening
        self._years_in_business: float = 0.0

    @property
    def status(self) -> BusinessStatus:
        return self._status

    @property
    def years_in_business(self) -> int:
        return math.floor(self._years_in_business)

    def on_add(self) -> None:
        self.get_type().instances += 1

    def on_remove(self) -> None:
        self.get_type().instances -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_def": self.business_def.name,
            "name": self._name,
            "operating_hours": self.business_def.hours,
            "open_positions": self._open_positions,
            "employees": self._employees,
            "owner": self._owner if self._owner else -1,
        }

    def get_owner(self) -> Optional[int]:
        return self._owner

    def needs_owner(self) -> bool:
        return self._owner is None and self.get_type().owner_type is not None

    def get_open_positions(self) -> List[str]:
        return [title for title, n in self._open_positions.items() if n > 0]

    def get_type(self) -> BusinessDefinition:
        return self.business_def

    def get_name(self) -> str:
        return self._name

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

    def set_owner(self, character: Optional[int]) -> None:
        """Set the owner for this business"""
        self._owner = character

    def set_business_status(self, status: BusinessStatus) -> None:
        self._status = status

    def increment_years_in_business(self, years: float) -> None:
        self._years_in_business += years

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(type='{}', name='{}', owner={}, employees={}, openings={})".format(
            self.__class__.__name__,
            self.business_def.name,
            self._name,
            self._owner,
            self._employees,
            self._open_positions,
        )

    @classmethod
    def create(cls, world: World, **kwargs) -> Business:
        engine = world.get_resource(NeighborlyEngine)
        type_name: str = kwargs["business_type"]

        business_type = BusinessDefinition.get_registered_type(type_name)

        name = (
            engine.name_generator.get_name(business_type.name_pattern)
            if business_type.name_pattern
            else type_name
        )

        return Business(business_type, name)

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
