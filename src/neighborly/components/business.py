"""Components for businesses and business-related relationship statuses.

"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
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
    final,
)

import attrs

from neighborly.components.shared import (
    Building,
    FrequentedBy,
    Lifespan,
    Location,
    Name,
    Position2D,
)
from neighborly.ecs import Component, Event, GameObject, ISerializable, World
from neighborly.life_event import EventHistory, EventLog, LifeEvent
from neighborly.relationship import Relationships
from neighborly.roles import IRole
from neighborly.spawn_table import BusinessSpawnTable, BusinessSpawnTableEntry
from neighborly.statuses import IStatus, Statuses
from neighborly.time import SimDateTime
from neighborly.world_map import BuildingMap


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


class Occupation(IRole, ABC):
    """Information about a character's employment status."""

    __slots__ = "start_year", "business"

    business: GameObject
    """The business they work for."""

    start_year: int
    """The year they started this occupation."""

    social_status: ClassVar[int] = 1
    """The socioeconomic status associated with this occupation."""

    job_requirements: ClassVar[JobRequirements] = JobRequirements()
    """Requirements that characters need to meet to hold this occupation."""

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


@attrs.define(frozen=True)
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


class ServiceType(enum.IntFlag):
    """Services offered by businesses.

    Notes
    -----
    These categories were sourced from the following:
    - https://incorporated.zone/type-of-industries
    - https://www.indeed.com/career-advice/career-development/business-services-types
    """

    Agricultural = enum.auto()
    Alcohol = enum.auto()
    Automotive = enum.auto()
    ChildCare = enum.auto()
    Computer = enum.auto()
    Consulting = enum.auto()
    Construction = enum.auto()
    Creative = enum.auto()
    Cultural = enum.auto()
    Education = enum.auto()
    Entertainment = enum.auto()
    Fashion = enum.auto()
    Financial = enum.auto()
    Food = enum.auto()
    Gambling = enum.auto()
    HealthCare = enum.auto()
    Hospitality = enum.auto()
    Insurance = enum.auto()
    Legal = enum.auto()
    Leisure = enum.auto()
    Lodging = enum.auto()
    Manufacturing = enum.auto()
    Media = enum.auto()
    Mining = enum.auto()
    Pharmaceutical = enum.auto()
    PublicService = enum.auto()
    RealEstate = enum.auto()
    Recreation = enum.auto()
    Research = enum.auto()
    Retail = enum.auto()
    Security = enum.auto()
    Socializing = enum.auto()
    Software = enum.auto()
    Transport = enum.auto()


class Services(Component, ISerializable):
    """Tracks a set of services offered by a business."""

    __slots__ = "_services"

    _services: ServiceType
    """Service names."""

    def __init__(self, services: ServiceType = ServiceType(0)) -> None:
        """
        Parameters
        ----------
        services
            A starting set of service types.
        """
        super().__init__()
        self._services = services

    def __contains__(self, services: ServiceType) -> bool:
        return services in self._services

    def __str__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._services)

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._services)

    def to_dict(self) -> Dict[str, Any]:
        return {"services": list(self._services)}

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any) -> Services:
        service_names: List[str] = kwargs.get("services", [])

        services = ServiceType(0)

        for name in service_names:
            services |= ServiceType[name]

        return Services(services)


class ClosedForBusiness(IStatus):
    """Tags a business as closed and no longer active in the simulation."""

    is_persistent = True


class OpenForBusiness(IStatus):
    """Tags a business as actively conducting business in the simulation."""

    pass


class Business(Component, ISerializable):
    """Businesses are places where characters are employed."""

    __slots__ = (
        "_owner_position",
        "_employees",
        "_employee_positions",
        "_owner",
        "_business_type",
    )

    _owner_position: Type[Occupation]
    """The job position information for the business owner."""

    _employee_positions: Dict[Type[Occupation], int]
    """The positions available to work at this business."""

    _employees: Dict[GameObject, Type[Occupation]]
    """The Employee GameObjects mapped to their occupation roles."""

    _owner: Optional[GameObject]
    """The owner of the business."""

    _business_type: BusinessType
    """A reference to the businesses' BusinessType component"""

    def __init__(
        self,
        owner_type: Type[Occupation],
        employee_types: Dict[Type[Occupation], int],
        business_type: BusinessType,
    ) -> None:
        """
        Parameters
        ----------
        owner_type
            The OccupationType for the owner of the business.
        employee_types
            OccupationTypes mapped to the total number of that occupation that can work
            at an instance of this
            business.
        """
        super().__init__()
        self._owner_position = owner_type
        self._employee_positions = employee_types
        self._employees = {}
        self._owner = None
        self._business_type = business_type

    @property
    def owner_type(self) -> Type[Occupation]:
        """The name of the occupation type of the business' owner."""
        return self._owner_position

    @property
    def owner(self) -> Optional[GameObject]:
        return self._owner

    @property
    def business_type(self) -> BusinessType:
        return self._business_type

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


class BossOf(IStatus):
    """Tags the owner of a relationship as being the employer of the target."""

    pass


class EmployeeOf(IStatus):
    """Tags the owner of a relationship as being the employee of the target."""

    pass


class CoworkerOf(IStatus):
    """Tags the owner of a relationship as being a coworker of the target."""

    pass


@attrs.define
class BusinessConfig:
    owner_type: Type[Occupation]
    employee_types: Dict[Type[Occupation], int] = attrs.field(factory=dict)
    spawn_frequency: int = 1
    max_instances: int = 9999
    min_population: int = 0
    year_available: int = 0
    year_obsolete: int = 9999
    lifespan: int = 15
    services: Tuple[str, ...] = attrs.field(factory=tuple)


class BusinessType(Component, ABC):
    """Defines configuration information for GameObject instances of a business Type."""

    config: ClassVar[BusinessConfig]

    @classmethod
    def on_register(cls, world: World) -> None:
        world.resource_manager.get_resource(BusinessSpawnTable).update(
            BusinessSpawnTableEntry(
                name=cls.__name__,
                spawn_frequency=cls.config.spawn_frequency,
                max_instances=cls.config.max_instances,
                min_population=cls.config.min_population,
                year_available=cls.config.year_available,
                year_obsolete=cls.config.year_obsolete,
            )
        )

    @classmethod
    @abstractmethod
    def _instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        raise NotImplementedError

    @classmethod
    @final
    def instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        """Create a new GameObject instance of the given business type.

        Parameters
        ----------
        world
            The world to spawn the business into
        **kwargs
            Keyword arguments to pass to the BusinessType's factory

        Returns
        -------
        GameObject
            the instantiated business
        """
        business = cls._instantiate(world, **kwargs)

        BusinessCreatedEvent(world, business).dispatch()

        return business


class BaseBusiness(BusinessType):
    @classmethod
    def _instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        business = world.gameobject_manager.spawn_gameobject(
            components={
                Name: {"value": cls.__name__},
                Statuses: {},
                Relationships: {},
                Location: {},
                FrequentedBy: {},
                EventHistory: {},
                Building: {"building_type": "commercial"},
                Services: {"services": cls.config.services},
                cls: {},
            }
        )

        if lifespan := cls.config.lifespan:
            business.add_component(Lifespan, value=lifespan)

        business.add_component(
            Business,
            owner_type=cls.config.owner_type,
            employee_types=cls.config.employee_types,
            business_type=business.get_component(cls),
        )

        business.prefab = cls.__name__
        business.name = f"{cls.__name__}({business.uid})"

        current_date = business.world.resource_manager.get_resource(SimDateTime)
        building_map = business.world.resource_manager.get_resource(BuildingMap)
        business_spawn_table = business.world.resource_manager.get_resource(
            BusinessSpawnTable
        )

        lot: Tuple[int, int] = kwargs.get("lot")
        if lot is None:
            raise TypeError(
                "{}.instantiate is missing required keyword argument: 'lot'.".format(
                    cls.__name__
                )
            )

        # Increase the count of this business type in the settlement
        business_spawn_table.increment_count(
            type(business.get_component(Business).business_type).__name__
        )

        # Reserve the space
        building_map.add_building(lot, business)

        # Set the position of the building
        business.add_component(Position2D, x=lot[0], y=lot[1])

        # Mark the business open and active
        business.add_component(OpenForBusiness, timestamp=current_date.year)

        return business


class BusinessCreatedEvent(Event):
    __slots__ = "_business"

    def __init__(
        self,
        world: World,
        business: GameObject,
    ) -> None:
        super().__init__(world)
        self._business = business

    @property
    def business(self) -> GameObject:
        return self._business


class BusinessClosedEvent(LifeEvent):
    __slots__ = "business"

    business: GameObject

    def __init__(self, world: World, date: SimDateTime, business: GameObject) -> None:
        super().__init__(world, date)
        self.business = business

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.business.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "business": self.business}

    def __str__(self) -> str:
        return "{} [@ {}] {} closed for business".format(
            type(self).__name__,
            str(self.timestamp),
            self.business.name,
        )


class StartJobEvent(LifeEvent):
    __slots__ = "character", "business", "occupation"

    character: GameObject
    business: GameObject
    occupation: Type[Occupation]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: Type[Occupation],
    ) -> None:
        super().__init__(world, date)
        self.character = character
        self.business = business
        self.occupation = occupation

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "occupation": self.occupation.__name__,
        }

    def __str__(self) -> str:
        return "{} [@ {}] '{}' started a new job at '{}' as a '{}'.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
            self.business.name,
            self.occupation.__name__,
        )


class EndJobEvent(LifeEvent):
    __slots__ = "character", "business", "occupation", "reason"

    character: GameObject
    business: GameObject
    occupation: Type[Occupation]
    reason: Optional[LifeEvent]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: Type[Occupation],
        reason: Optional[LifeEvent] = None,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        self.character = character
        self.business = business
        self.occupation = occupation
        self.reason: Optional[LifeEvent] = reason

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "reason": self.reason.event_id if self.reason else -1,
        }

    def __str__(self) -> str:
        return "{} [@ {}] {} ended their job at '{}' as a '{}'.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
            self.business.name,
            self.occupation.__name__,
        )


class StartBusinessEvent(LifeEvent):
    __slots__ = "character", "business", "occupation"

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: Type[Occupation],
    ) -> None:
        super().__init__(world, date)
        self.character = character
        self.business = business
        self.occupation = occupation

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.business.get_component(EventHistory).append(self)
        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "occupation": self.occupation.__name__,
        }

    def __str__(self) -> str:
        return "{} [@ {}] {} started a business '{}'.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
            self.business.name,
        )


class RetirementEvent(LifeEvent):
    __slots__ = "character", "business", "occupation"

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: Type[Occupation],
    ) -> None:
        super().__init__(world, date)
        self.character = character
        self.business = business
        self.occupation = occupation

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "occupation": self.occupation.__name__,
        }

    def __str__(self) -> str:
        return "{} [@ {}] {} retired from their position as '{}' at {}".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
            self.occupation.__name__,
            self.business.name,
        )


def location_has_services(location: GameObject, services: ServiceType) -> bool:
    """Check if the location has the given services

    Parameters
    ----------
    location
        The location to check.
    services
        Service types.

    Returns
    -------
    bool
        True if all the services are offered by the location, False otherwise.
    """
    services_comp = location.get_component(Services)
    return services in services_comp
