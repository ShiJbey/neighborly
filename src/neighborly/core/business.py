from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, IntFlag
from typing import Any, ClassVar, Dict, List, Optional, Protocol, Tuple, Type

from neighborly.core.ecs import Component, GameObject, World, EntityArchetype
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.position import Position2D
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

    Class Attributes
    ----------------
    _type_registry: Dict[str, OccupationType]
        Registered instances of OccupationTypes
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


class Occupation(Component):
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

    def on_remove(self) -> None:
        """Run when the component is removed from the GameObject"""
        world = self.gameobject.world
        workplace = world.get_gameobject(self._business).get_component(Business)
        if workplace.owner != self.gameobject.id:
            workplace.remove_employee(self.gameobject.id)


class BusinessServiceFlag(IntFlag):
    NONE = 0
    ALCOHOL = 1 << 0
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
        "services"
    )

    def __init__(
        self,
        business_type: str,
        name: str,
        owner_type: str = None,
        owner: int = None,
        open_positions: Dict[str, int] = None,
        operating_hours: Dict[str, List[RoutineEntry]] = None,
        services: BusinessServiceFlag = BusinessServiceFlag.NONE,
    ) -> None:
        super().__init__()
        self.business_type: str = business_type
        self.owner_type: Optional[str] = owner_type
        self.name: str = name
        # self._operating_hours: Dict[str, List[RoutineEntry]] = self._create_routines(
        #     parse_schedule_str(business_def.hours)
        # )
        self.operating_hours: Dict[str, List[RoutineEntry]] = operating_hours if operating_hours else {}
        self._open_positions: Dict[str, int] = open_positions if open_positions else {}
        self._employees: Dict[int, str] = {}
        self.owner: Optional[int] = owner
        self.status: BusinessStatus = BusinessStatus.PendingOpening
        self._years_in_business: float = 0.0
        self.services: BusinessServiceFlag = services

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
            "employees": self.employees,
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
        business_name: str = engine.name_generator.get_name(kwargs.get("name_format", business_type))
        owner_type: Optional[str] = kwargs.get("owner_type")
        employee_types: Dict[str, int] = kwargs.get("employees_types", {})
        services: BusinessServiceFlag = kwargs.get("services", BusinessServiceFlag.NONE)
        # operating_hours: Dict[str, List[RoutineEntry]] = self._create_routines(
        #     parse_schedule_str(business_def.hours)
        # )

        return Business(
            business_type=business_name,
            name=business_name,
            open_positions=employee_types,
            services=services,
            owner_type=owner_type
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


class BusinessArchetype(EntityArchetype):
    """
    Shared information about all businesses that
    have this type
    """

    __slots__ = "hours", "name_format", "owner_type", "max_instances", \
                "min_population", "employee_types", "services", "service_flags", \
                "spawn_multiplier"

    def __init__(
        self,
        name: str,
        hours: str,
        name_format: str = None,
        owner_type: str = None,
        max_instances: int = 9999,
        min_population: int = 0,
        employee_types: Dict[str, int] = None,
        services: List[str] = None,
        spawn_multiplier: int = 1,
        extra_components: Dict[Type[Component], Dict[str, Any]] = None
    ) -> None:
        super().__init__(name)
        self.hours: str = hours
        self.name_format: str = name_format if name_format else name
        self.owner_type: Optional[str] = owner_type
        self.max_instances: int = max_instances
        self.min_population: int = min_population
        self.employee_types: Dict[str, int] = employee_types if employee_types else {}
        self.services: List[str] = services if services else {}
        self.service_flags: BusinessServiceFlag = BusinessServiceFlag.NONE
        self.spawn_multiplier: int = spawn_multiplier
        for service_name in self.services:
            self.service_flags |= BusinessServiceFlag[
                service_name.strip().upper().replace(" ", "_")
            ]

        self.add(
            Business,
            business_type=self.name,
            name_format=self.name_format,
            hours=self.hours,
            owner_type=self.owner_type,
            employee_types=self.employee_types,
            services=self.service_flags
        )
        self.add(Location)
        self.add(Position2D)

        if extra_components:
            for component_type, params in extra_components.items():
                self.add(component_type, **params)


class BusinessArchetypeLibrary:
    _registry: Dict[str, BusinessArchetype] = {}

    @classmethod
    def register(cls, archetype: BusinessArchetype, name: str = None, ) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name if name else archetype.name] = archetype

    @classmethod
    def get_all(cls) -> List[BusinessArchetype]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> BusinessArchetype:
        """Get a LifeEventType using a name"""
        return cls._registry[name]
