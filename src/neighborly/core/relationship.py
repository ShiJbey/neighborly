import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any

FRIENDSHIP_MAX: float = 50
FRIENDSHIP_MIN: float = -50

ROMANCE_MAX: float = 50
ROMANCE_MIN: float = -50

SALIENCE_MAX: float = 100
SALIENCE_MIN: float = 0
SALIENCE_INCREMENT: float = 2


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


@dataclass(frozen=True)
class RelationshipTag:
    name: str
    friendship: float = 0
    romance: float = 0
    salience: float = 0
    requirements: List[Callable[['Relationship'], bool]] = \
        field(default_factory=list)


class Relationship:
    """
    Relationships are one of the core factors of a
    social simulation next to the characters. They
    track how one character feels about another. And
    they evolve as a function of how many times two
    characters interact.
    """

    __slots__ = (
        "_base_salience",
        "_romance",
        "_romance_increment",
        "_friendship",
        "_friendship_increment",
        "_tags",
        "_salience",
        "_target",
        "_owner",
        "_is_dirty",
    )

    _registered_tags: Dict[str, RelationshipTag] = {}

    def __init__(
            self,
            owner: int,
            target: int,
    ) -> None:
        self._base_salience: float = 0
        self._friendship: float = 0
        self._romance: float = 0
        self._romance_increment: float = 0
        self._friendship_increment: float = 0
        self._salience: float = 0
        self._is_dirty: bool = True
        self._tags: Dict[str, RelationshipTag] = {}
        self._target: int = target
        self._owner: int = owner

    @property
    def target(self) -> int:
        return self._target

    @property
    def owner(self) -> int:
        return self._owner

    @property
    def friendship(self) -> int:
        if self._is_dirty:
            self._recalculate_stats()
        return math.floor(self._friendship)

    @property
    def romance(self) -> int:
        if self._is_dirty:
            self._recalculate_stats()
        return math.floor(self._romance)

    @property
    def salience(self) -> int:
        if self._is_dirty:
            self._recalculate_stats()
        return math.floor(self._salience)

    @property
    def tags(self) -> Dict[str, RelationshipTag]:
        return self._tags

    def add_tag(self, modifier: RelationshipTag) -> None:
        self._tags[modifier.name] = modifier
        self._is_dirty = True

    def remove_tag(self, modifier: RelationshipTag) -> None:
        del self._tags[modifier.name]
        self._is_dirty = True

    def has_tags(self, *names: str) -> bool:
        return all([name in self._tags for name in names])

    def update(self) -> None:
        if self._is_dirty:
            self._recalculate_stats()

        self._base_salience += SALIENCE_INCREMENT
        self._friendship = clamp(
            self._friendship + self._friendship_increment, FRIENDSHIP_MIN, FRIENDSHIP_MAX
        )
        self._romance = clamp(self._romance + self._romance_increment, ROMANCE_MIN, ROMANCE_MAX)

        for tag in [*self._tags.values()]:
            reqs_pass = all([fn(self)
                             for fn in tag.requirements]) if tag.requirements else True
            if not reqs_pass:
                self.remove_tag(tag)

        # Loop through all tags and apply valid ones
        for tag in self._registered_tags.values():
            if tag.name in self._tags:
                continue

            reqs_pass = all([fn(self)
                             for fn in tag.requirements]) if tag.requirements else True
            if reqs_pass:
                self.add_tag(tag)

        self._is_dirty = True

    def _recalculate_stats(self) -> None:
        self._romance_increment = 0
        self._friendship_increment = 0
        self._salience = self._base_salience

        for modifier in self._tags.values():
            self._salience += modifier.salience
            self._romance_increment += modifier.romance
            self._friendship_increment += modifier.friendship

        self._salience = clamp(self._salience, SALIENCE_MIN, SALIENCE_MAX)

        self._is_dirty = False

    def __repr__(self) -> str:
        return "{}(owner={}, target={}, romance={}, friendship={}, salience={}, tags={})".format(
            self.__class__.__name__,
            self.owner,
            self.target,
            self.romance,
            self.friendship,
            self.salience,
            list(self._tags.keys()),
        )

    @classmethod
    def get_tag(cls, name: str) -> RelationshipTag:
        return cls._registered_tags[name]

    @classmethod
    def register_tag(cls, tag: RelationshipTag) -> None:
        cls._registered_tags[tag.name] = tag


################################################
#          PARSING RELATIONSHIP TAGS           #
################################################

def _ineq_check(attr: str, op: str, val: float) -> Callable[['Relationship'], bool]:
    """Perform equality/inequality check on a Relationship's attribute"""

    def check_fn(obj: 'Relationship') -> bool:
        attr_val = getattr(obj, attr)
        if op == '=':
            return attr_val == val
        elif op == '<':
            return attr_val < val
        elif op == '>':
            return attr_val > val
        elif op == '<=':
            return attr_val <= val
        elif op == '>=':
            return attr_val >= val
        else:
            raise ValueError(f"Invalid inequality operation {op}")

    return check_fn


def _tag_check(*tags) -> Callable[['Relationship'], bool]:
    """Check if a Relationship has given tags"""

    def check_fn(obj: 'Relationship') -> bool:
        return obj.has_tags(*tags)

    return check_fn


def parse_requirements_str(requirements_str: str) -> List[Callable[['Relationship'], bool]]:
    """Parse requirement strings from RelationshipTag definitions and create callables"""
    clauses = list(map(str.strip, requirements_str.split("AND")))

    check_fns: List[Callable[['Relationship'], bool]] = []

    for clause in clauses:
        clause_tuple = tuple(map(str.strip, clause.split(" ")))

        if len(clause_tuple) == 2:
            op, value = clause_tuple
            if op == 'hasTag':
                check_fns.append(_tag_check(value))
            elif op == 'hasTags':
                # Split the params
                tags_to_check = tuple(map(str.strip, value.split(",")))
                check_fns.append(_tag_check(*tags_to_check))
            else:
                raise ValueError(f"Invalid operation: {op} in '{clause}'")

        elif len(clause_tuple) == 3:
            attr, op, val = clause_tuple
            check_fns.append(_ineq_check(attr, op, float(val)))
        else:
            raise ValueError(f"Clause has too many terms: {clause}")

    return check_fns


def load_relationship_tags(tags: List[Dict[str, Any]]) -> None:
    """Load relationship tags from list of dicts"""

    for tag_data in tags:
        requirements_str = tag_data.get('requirements')

        requirements = parse_requirements_str(requirements_str) if requirements_str else []

        creation_data = {**tag_data, 'requirements': requirements}

        Relationship.register_tag(RelationshipTag(**creation_data))
