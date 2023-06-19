from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
)

import pyparsing as pp
from pyparsing import pyparsing_common as ppc
from ordered_set import OrderedSet

from neighborly.core.ecs import World, Component, GameObject, ISerializable
from neighborly.core.relationship import RelationshipStatus
from neighborly.core.status import StatusComponent
from neighborly.core.time import SimDateTime, Weekday

from neighborly.core.ecs import EntityPrefab, GameObjectFactory


class Occupation(Component, ISerializable):
    """Information about a character's employment status."""

    __slots__ = "_occupation_type", "_start_date", "_business"

    _occupation_type: GameObject
    """The name of the occupation."""

    _business: int
    """The GameObjectID of the business they work for."""

    _start_date: SimDateTime
    """The date they started this occupation."""

    def __init__(
        self, occupation_type: GameObject, business: int, start_date: SimDateTime
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
            "occupation_type": self._occupation_type.uid,
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
    def occupation_type(self) -> GameObject:
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
    """Tracks a set of services offered by a business.

    Notes
    -----
    Service names are case-insensitive and are all converted to lowercase upon storage.
    """

    __slots__ = "_services"

    _services: OrderedSet[str]
    """Service names."""

    def __init__(self, services: Optional[Iterable[str]] = None) -> None:
        """
        Parameters
        ----------
        services
            A starting set of service names.
        """
        super().__init__()
        self._services = OrderedSet([])

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
        service
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
        return {"hours": {str(day): list(hours) for day, hours in self._hours.items()}}


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


class OccupationType(Component, ISerializable):
    """Shared information about all occupations with this type."""

    def to_dict(self) -> Dict[str, Any]:
        return {}

    def __str__(self) -> str:
        return type(self).__name__

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class SocialStatusLevel(Component, ISerializable):
    __slots__ = "_status_level"

    _status_level: int

    def __init__(self, status_level: int) -> None:
        super().__init__()
        self._status_level = status_level

    @property
    def status_level(self) -> int:
        return self._status_level

    def to_dict(self) -> Dict[str, Any]:
        return {"status_level": self._status_level}

    def __str__(self) -> str:
        return f"{type(self).__name__}(status_level={self.status_level})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(status_level={self.status_level})"


class JobRequirements(Component):
    """Specifies precondition functions for occupations."""

    def __init__(self, rules: list[Callable[[GameObject], bool]]) -> None:
        super().__init__()
        self.rules = rules


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


class _PreconditionWrapper(Protocol):
    def __call__(self, *args: Any) -> Callable[[GameObject], bool]:
        raise NotImplementedError


class JobRequirementLibrary:
    def __init__(self) -> None:
        self.rules: dict[str, _PreconditionWrapper] = {}

    def add(self, name: str, fn_wrapper: _PreconditionWrapper) -> None:
        self.rules[name] = fn_wrapper


class JobRequirementParser:
    """Parses strings specifying preconditions for characters to have certain roles.

    Preconditions are specified using a Lisp-style prefix-notation. For example,

    (AND
        (has_component 'CollegeGraduate')
        (OR
            (has_gender 'Male')
            (has_gender 'Female')
            (over_age 45)
        )
    )
    """

    __slots__ = "_grammar", "_world"

    _grammer: pp.ParserElement
    """The grammar used to parse requirement strings."""

    _world: World
    """The world instance to sample precondition functions from."""

    def __init__(self, world: World) -> None:
        self._grammar = JobRequirementParser._initialize_grammar()
        self._world = world

    @staticmethod
    def _initialize_grammar() -> pp.ParserElement:
        # Convert keywords to python values
        TRUE = JobRequirementParser._make_keyword(
            "true", True
        ) | JobRequirementParser._make_keyword("True", False)
        FALSE = JobRequirementParser._make_keyword(
            "false", False
        ) | JobRequirementParser._make_keyword("False", False)
        NULL = JobRequirementParser._make_keyword("null", None)

        # Track parentheses and brackets, but don't include in output
        LPAREN = pp.Suppress("(")
        RPAREN = pp.Suppress(")")

        # Set up capturing string and number values
        string_val = pp.QuotedString("'") | pp.QuotedString('"')
        number_val = ppc.number()  # type: ignore

        # Arguments lists require zero or more values
        fn_args = pp.Group(
            pp.ZeroOrMore(string_val | number_val | TRUE | FALSE | NULL)  # type: ignore
        )

        # Identifier catches an python-allowed identifier name
        func_name = ppc.identifier

        # Refers to any complete expression
        expr = pp.Forward().set_name("expr")

        # A single clause contains a function name and arguments surrounded by
        # parenthesis
        clause = LPAREN + pp.Group(func_name + fn_args) + RPAREN  # type: ignore
        and_expr = LPAREN + pp.Group("AND" + pp.Group(expr + pp.OneOrMore(expr))) + RPAREN  # type: ignore
        or_expr = LPAREN + pp.Group("OR" + pp.Group(expr + pp.OneOrMore(expr))) + RPAREN  # type: ignore

        expr <<= clause | and_expr | or_expr  # type: ignore

        program: pp.ParserElement = expr + pp.string_end  # type: ignore

        return cast(pp.ParserElement, program)  # type: ignore

    @staticmethod
    def _make_keyword(kwd_str: str, kwd_value: Any):
        keyword = pp.Keyword(kwd_str).set_parse_action(pp.replaceWith(kwd_value))  # type: ignore
        return keyword

    def parse_string(self, input_str: str) -> Callable[[GameObject], bool]:
        """Parse a string into a rule."""

        results = self._grammar.parse_string(input_str, parse_all=True)  # type: ignore
        rule_data = cast(list[Any], results.as_list()[0])  # type: ignore

        rule = self._process_expr(rule_data)  # type: ignore

        return rule

    def _process_expr(self, expr: list[Any]) -> Callable[[GameObject], bool]:
        op_name: str = expr[0]
        op_args: list[Any] = expr[1]

        if op_name == "AND":
            # Logical-AND of multiple expressions
            sub_expressions = [self._process_expr(sub_expr) for sub_expr in op_args]

            return lambda gameobject: all(
                [precond(gameobject) for precond in sub_expressions]
            )

        elif op_name == "OR":
            # Logical-OR of multiple expressions
            sub_expressions = [self._process_expr(sub_expr) for sub_expr in op_args]

            return lambda gameobject: any(
                [precond(gameobject) for precond in sub_expressions]
            )

        else:
            library = self._world.get_resource(JobRequirementLibrary)
            return library.rules[op_name](*op_args)


class OccupationLibrary:
    """Manages runtime type information for items"""

    __slots__ = "_occupations"

    _occupations: Dict[str, GameObject]

    def __init__(self) -> None:
        self._occupations = {}

    @property
    def occupations(self) -> Dict[str, GameObject]:
        return self._occupations


def add_occupation_type(world: World, prefab: EntityPrefab):
    factory = world.get_resource(GameObjectFactory)
    factory.add(prefab)
    occupation_type = factory.instantiate(world, prefab.name)
    occupation_type.name = prefab.name
    world.get_resource(OccupationLibrary).occupations[
        occupation_type.name
    ] = occupation_type


def get_occupation_type(world: World, occupation_name: str) -> GameObject:
    return world.get_resource(OccupationLibrary).occupations[occupation_name]
