"""Components for businesses and business-related relationship statuses.

"""

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
    cast,
)

import pyparsing as pp
from ordered_set import OrderedSet
from pyparsing import pyparsing_common as ppc

from neighborly.components.shared import Name
from neighborly.core.ecs import (
    Component,
    GameObjectPrefab,
    GameObject,
    ISerializable,
    TagComponent,
    World,
)
from neighborly.core.life_event import LifeEvent
from neighborly.core.relationship import RelationshipStatus
from neighborly.core.status import StatusComponent
from neighborly.core.time import SimDateTime


class Occupation(Component, ISerializable):
    """Information about a character's employment status."""

    __slots__ = "_occupation_type", "_start_date", "_business"

    _occupation_type: GameObject
    """Shared occupation definition data."""

    _business: GameObject
    """The business they work for."""

    _start_date: SimDateTime
    """The date they started this occupation."""

    def __init__(
        self, occupation_type: GameObject, business: GameObject, start_date: SimDateTime
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
            "occupation_type": self._occupation_type.name,
            "business": self._business.uid,
            "start_date": str(self._start_date),
        }

    @property
    def business(self) -> GameObject:
        """The business they work for."""
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

    occupation_type: GameObject
    """The name of the job held."""

    business: GameObject
    """The GameObjectID ID of the business the character worked at."""

    years_held: float = 0
    """The number of years the character held this job."""

    reason_for_leaving: Optional[LifeEvent] = None
    """Name of the event that caused the character to leave this job."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "occupation_type": self.occupation_type.name,
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
        occupation_type: GameObject,
        business: GameObject,
        years_held: float,
        reason_for_leaving: Optional[LifeEvent] = None,
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


class ServiceType(TagComponent):
    """Tags a GameObject as being a type of service offered by a business."""

    pass


class Services(Component, ISerializable):
    """Tracks a set of services offered by a business.

    Notes
    -----
    Service names are case-insensitive and are all converted to lowercase upon storage.
    """

    __slots__ = "_services"

    _services: OrderedSet[GameObject]
    """Service names."""

    def __init__(self, services: Optional[Iterable[GameObject]] = None) -> None:
        """
        Parameters
        ----------
        services
            A starting set of service names.
        """
        super().__init__()
        self._services = OrderedSet(services if services else [])

    def __iter__(self) -> Iterator[GameObject]:
        return self._services.__iter__()

    def __contains__(self, service: GameObject) -> bool:
        return service in self._services

    def __str__(self) -> str:
        return ", ".join([s.name for s in self._services])

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__, str([s.name for s in self._services])
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"services": [s.name for s in self._services]}


class ServiceLibrary:
    """A collection of references to service type GameObject instances."""

    __slots__ = "_service_types", "_services_to_instantiate"

    _services_to_instantiate: OrderedSet[str]
    """The names of service prefabs to instantiate at the start of the simulation."""

    _service_types: Dict[str, GameObject]
    """Service type names mapped to their GameObject instances."""

    def __init__(self) -> None:
        self._service_types = {}
        self._services_to_instantiate = OrderedSet([])

    @property
    def services_to_instantiate(self) -> OrderedSet[str]:
        return self._services_to_instantiate

    def add(self, service: GameObject) -> None:
        """Add a service type to the library.

        Parameters
        ----------
        service
            An service type GameObject.
        """
        self._service_types[service.name] = service

    def get(self, name: str) -> GameObject:
        """Retrieve a service type entity.

        Parameters
        ----------
        name
            The name of a service type.

        Returns
        -------
        GameObject
            An service type entity.
        """
        return self._service_types[name]


class ClosedForBusiness(StatusComponent):
    """Tags a business as closed and no longer active in the simulation."""

    is_persistent = True


class OpenForBusiness(StatusComponent):
    """Tags a business as actively conducting business in the simulation."""

    pass


class Business(Component, ISerializable):
    """Businesses are places where characters are employed."""

    __slots__ = ("_owner_type", "_employees", "_open_positions", "_owner")

    _owner_type: GameObject
    """The occupation type of the business owner."""

    _open_positions: Dict[GameObject, int]
    """Occupation types mapped to the number of open positions."""

    _employees: Dict[GameObject, GameObject]
    """The Employee GameObjects mapped to their occupation roles."""

    _owner: Optional[Tuple[GameObject, GameObject]]
    """The GameObjectID of the owner of this business."""

    def __init__(
        self,
        owner_type: GameObject,
        employee_types: Dict[GameObject, int],
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
    def owner(self) -> Optional[GameObject]:
        """The GameObject ID of the owner of the business."""
        if self._owner:
            return self._owner[0]
        return None

    @property
    def owner_type(self) -> GameObject:
        """The name of the occupation type of the business' owner."""
        return self._owner_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner_type": self.owner_type.name,
            "open_positions": {
                occupation_type.name: slots
                for occupation_type, slots in self._open_positions.items()
            },
            "employees": [
                {
                    "title": role.get_component(Name).value,
                    "uid": employee.uid,
                }
                for employee, role in self._employees.items()
            ],
            "owner": {
                "title": self._owner_type.get_component(Name).value,
                "uid": self._owner[0].uid if self._owner else -1,
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

    def get_open_positions(self) -> List[GameObject]:
        """Get all the open job titles.

        Returns
        -------
        List[str]
            All the names of all open positions at the business.
        """
        return [
            occupation_type
            for occupation_type, count in self._open_positions.items()
            if count > 0
        ]

    def iter_employees(self) -> Iterator[Tuple[GameObject, GameObject]]:
        """Get all current employees.

        Returns
        -------
        List[int]
            Returns the GameObject IDs of all employees of this business.
        """
        return self._employees.items().__iter__()

    def set_owner(self, owner: Optional[Tuple[GameObject, GameObject]]) -> None:
        """Set the ID for the owner of the business.

        Parameters
        ----------
        owner
            An entry for the new owner and their role, or None if removing the owner.
        """
        self._owner = owner

    def add_employee(self, employee: GameObject, role: GameObject) -> None:
        """Add employee and remove a vacant position.

        Parameters
        ----------
        employee
            The GameObject ID of the employee.
        role
            The name of the employee's position.
        """
        self._employees[employee] = role
        self._open_positions[role.get_component(Occupation).occupation_type] -= 1

    def remove_employee(self, employee: GameObject) -> None:
        """Remove an employee and vacate their position.

        Parameters
        ----------
        employee
            The GameObject representing an employee.
        """
        role = self._employees[employee]
        self._open_positions[role.get_component(Occupation).occupation_type] += 1
        del self._employees[employee]

    def get_employee_role(self, employee: GameObject) -> GameObject:
        """Get the occupation role associated with this employee.

        Parameters
        ----------
        employee
            The employee to get the role for

        Returns
        -------
        GameObject
            Their occupation role
        """
        return self._employees[employee]

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
    """The socioeconomic status associated with an occupation type."""

    __slots__ = "_status_level"

    _status_level: int
    """The status level with higher value meaning higher status."""

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
    """Specifies precondition rules for an occupation type."""

    __slots__ = "_rules"

    _rules: Tuple[Callable[[GameObject], bool], ...]
    """A collection of preconditions."""

    def __init__(self, rules: Iterable[Callable[[GameObject], bool]]) -> None:
        super().__init__()
        self._rules = tuple(rules)

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
        for rule in self._rules:
            if rule(gameobject):
                return True
        return False


class BusinessOwner(StatusComponent):
    """Tags a GameObject as being the owner of a business."""

    __slots__ = "business"

    business: GameObject
    """The business owned."""

    def __init__(self, business: GameObject) -> None:
        """
        Parameters
        ----------
        business
            The business owned.
        """
        super().__init__()
        self.business: GameObject = business

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "business": self.business.uid}


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


class JobRequirementLibrary:
    """A shared collection of job requirement rule used by occupation type requirement prefabs."""

    __slots__ = "_rules"

    _rules: dict[str, JobRequirementFn]
    """String identifiers mapped to precondition functions."""

    def __init__(self) -> None:
        self._rules = {}

    def add(self, name: str, job_req_fn: JobRequirementFn) -> None:
        """Add a new job requirement rule.

        Parameters
        ----------
        name
            The name to associate with the rule.
        job_req_fn
            The function to add.
        """
        self._rules[name] = job_req_fn

    def get(self, rule_name: str) -> JobRequirementFn:
        """Retrieve a job requirement rule by name.

        Parameters
        ----------
        rule_name
            The name of a rule.

        Returns
        -------
        JobRequirementRule
            A job requirement rule.
        """
        return self._rules[rule_name]


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

    _grammar: pp.ParserElement
    """The grammar used to parse requirement strings."""

    _world: World
    """The world instance to sample precondition functions from."""

    def __init__(self, world: World) -> None:
        self._grammar = JobRequirementParser._initialize_grammar()
        self._world = world

    @staticmethod
    def _initialize_grammar() -> pp.ParserElement:
        """Initializes the grammar used by the parser."""

        # Convert keywords to python values
        _TRUE = JobRequirementParser._make_keyword(
            "true", True
        ) | JobRequirementParser._make_keyword("True", False)
        _FALSE = JobRequirementParser._make_keyword(
            "false", False
        ) | JobRequirementParser._make_keyword("False", False)
        _NULL = JobRequirementParser._make_keyword("null", None)

        # Track parentheses and brackets, but don't include in output
        _LPAREN = pp.Suppress("(")
        _RPAREN = pp.Suppress(")")

        # Set up capturing string and number values
        string_val = pp.QuotedString("'") | pp.QuotedString('"')
        number_val = ppc.number()  # type: ignore

        # Arguments lists require zero or more values
        fn_args = pp.Group(
            pp.ZeroOrMore(string_val | number_val | _TRUE | _FALSE | _NULL)  # type: ignore
        )

        # Identifier catches a python-allowed identifier name
        func_name = ppc.identifier

        # Refers to any complete expression
        expr = pp.Forward().set_name("expr")

        # A single clause contains a function name and arguments surrounded by
        # parenthesis
        clause = _LPAREN + pp.Group(func_name + fn_args) + _RPAREN  # type: ignore
        and_expr = _LPAREN + pp.Group("AND" + pp.Group(expr + pp.OneOrMore(expr))) + _RPAREN  # type: ignore
        or_expr = _LPAREN + pp.Group("OR" + pp.Group(expr + pp.OneOrMore(expr))) + _RPAREN  # type: ignore

        expr <<= clause | and_expr | or_expr  # type: ignore

        program: pp.ParserElement = expr + pp.string_end  # type: ignore

        return cast(pp.ParserElement, program)  # type: ignore

    @staticmethod
    def _make_keyword(kwd_str: str, kwd_value: Any) -> pp.ParserElement:
        """Turn a given string into a keyword for a grammar."""
        keyword = pp.Keyword(kwd_str).set_parse_action(pp.replaceWith(kwd_value))  # type: ignore

        if keyword is None:
            raise RuntimeError(f"Failed to create keyword: {kwd_str}")

        return keyword

    def parse_string(self, input_str: str) -> Precondition:
        """Parse a string into a precondition function.

        Parameters
        ----------
        input_str
            The string representation of a set of job requirement rules

        Returns
        -------
        Callable[[GameObject], bool]
            A callable precondition
        """

        results = self._grammar.parse_string(input_str, parse_all=True)  # type: ignore
        rule_data = cast(list[Any], results.as_list()[0])  # type: ignore

        rule = self._process_expr(rule_data)  # type: ignore

        return rule

    def _process_expr(self, expr: list[Any]) -> Precondition:
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
            try:
                return JobRequirementRule(
                    self._world.resource_manager.get_resource(
                        JobRequirementLibrary
                    ).get(op_name),
                    *op_args,
                )
            except KeyError:
                raise Exception(
                    f"No job requirement rule function found for name: {op_name}"
                )


class OccupationLibrary:
    """Manages runtime type information for occupation types."""

    __slots__ = "_occupations", "_occupations_to_instantiate"

    _occupations_to_instantiate: OrderedSet[str]
    """The names of occupations types to instantiate at the start of the simulation."""

    _occupations: Dict[str, GameObject]
    """Occupation names mapped to their GameObject instances."""

    def __init__(self) -> None:
        self._occupations_to_instantiate = OrderedSet([])
        self._occupations = {}

    @property
    def occupations_to_instantiate(self) -> OrderedSet[str]:
        return self._occupations_to_instantiate

    def add(self, occupation_type: GameObject) -> None:
        """Add an occupation type to the library.

        Parameters
        ----------
        occupation_type
            An occupation type entity.
        """
        self._occupations[occupation_type.name] = occupation_type

    def get(self, name: str) -> GameObject:
        """Retrieve an occupation type entity.

        Parameters
        ----------
        name
            The name of an occupation type.

        Returns
        -------
        GameObject
            An occupation type entity.
        """
        return self._occupations[name]


def register_occupation_type(world: World, prefab: GameObjectPrefab) -> None:
    """Register an occupation type for later use.

    Parameters
    ----------
    world
        The world instance to save the occupation type to.
    prefab
        GameObject prefab information about the occupation.
    """
    world.gameobject_manager.add_prefab(prefab)
    world.resource_manager.get_resource(
        OccupationLibrary
    ).occupations_to_instantiate.add(prefab.name)


def register_service_type(world: World, prefab: GameObjectPrefab) -> None:
    """Register a service type for later use.

    Parameters
    ----------
    world
        The world instance to save to service type to.
    prefab
        GameObject prefab information about the service type.
    """

    world.gameobject_manager.add_prefab(prefab)
    world.resource_manager.get_resource(ServiceLibrary).services_to_instantiate.add(
        prefab.name
    )
