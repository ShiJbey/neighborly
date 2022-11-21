from __future__ import annotations

from typing import Any, Dict, List, Set

from neighborly.core.ecs import Component


def clamp(value: int, minimum: int, maximum: int) -> int:
    """Clamp a floating point value within a min,max range"""
    return min(maximum, max(minimum, value))


class RelationshipStat:

    STAT_MAX: int = 50
    STAT_MIN: int = -50

    __slots__ = (
        "_raw_value",
        "_clamped_value",
        "_normalized_value",
        "_total_changes",
        "_positive_changes",
        "_negative_changes",
    )

    def __init__(self) -> None:
        self._raw_value: int = 0
        self._clamped_value: int = 0
        self._normalized_value: float = 0.5
        self._total_changes: int = 0
        self._positive_changes: int = 0
        self._negative_changes: int = 0

    @property
    def raw(self) -> int:
        return self._raw_value

    @property
    def clamped(self) -> int:
        return self._clamped_value

    @property
    def value(self) -> float:
        return self._normalized_value

    def increase(self, change: int) -> None:
        """Increase the stat by n-times the increment value"""
        self._total_changes += change
        self._positive_changes += change
        self._normalized_value = self._positive_changes / self._total_changes
        self._raw_value += change
        self._clamped_value = clamp(self._raw_value, self.STAT_MIN, self.STAT_MAX)

    def decrease(self, change: int) -> None:
        """Increase the stat by n-times the increment value"""
        self._total_changes += change
        self._negative_changes += change
        self._normalized_value = self._positive_changes / self._total_changes
        self._raw_value -= change
        self._clamped_value = clamp(self._raw_value, self.STAT_MIN, self.STAT_MAX)

    def __repr__(self) -> str:
        return "{}(value={}, clamped={}, raw={})".format(
            self.__class__.__name__, self.value, self.clamped, self.raw
        )

    def __lt__(self, other: float) -> bool:
        return self._normalized_value < other

    def __gt__(self, other: float) -> bool:
        return self._normalized_value > other

    def __le__(self, other: float) -> bool:
        return self._normalized_value <= other

    def __ge__(self, other: float) -> bool:
        return self._normalized_value <= other

    def __eq__(self, other: float) -> bool:
        return self._normalized_value == other

    def __ne__(self, other: float) -> bool:
        return self._normalized_value != other

    def __int__(self) -> int:
        return self._clamped_value

    def __float__(self) -> float:
        return self._normalized_value


class Relationship:
    """
    Relationships are one of the core factors of a
    social simulation next to the characters. They
    track how one entity feels about another. And
    they evolve as a function of how many times two
    characters interact.

    Class Attributes
    ----------------
    _registered_tags: Dict[str, RelationshipTag]
        All the tags that may be used during the simulation

    Attributes
    ----------
    _owner: int
        Character who owns the relationship
    _target: int
        The entity who this relationship is directed toward
    _friendship: RelationshipStat
        Friendship score on the scale [FRIENDSHIP_MIN, FRIENDSHIP_MAX]
        where a max means best friends and min means worst-enemies
    _romance: RelationshipStat
        Romance score on the scale [ROMANCE_MIN, ROMANCE_MAX]
        where a max is complete infatuation and the min is repulsion
    _tags: RelationshipTag
        All the tags that are attached to this
    """

    __slots__ = (
        "_owner",
        "_target",
        "_friendship",
        "_romance",
        "_tags",
    )

    def __init__(self, owner: int, target: int) -> None:
        self._owner: int = owner
        self._target: int = target
        self._friendship: RelationshipStat = RelationshipStat()
        self._romance: RelationshipStat = RelationshipStat()
        self._tags: Set[str] = set()

    @property
    def target(self) -> int:
        return self._target

    @property
    def owner(self) -> int:
        return self._owner

    @property
    def friendship(self) -> RelationshipStat:
        return self._friendship

    @property
    def romance(self) -> RelationshipStat:
        return self._romance

    def add_tags(self, *tags: str) -> None:
        """Return add a tag to this Relationship"""
        for tag in tags:
            self._tags.add(tag)

    def has_tag(self, tag: str) -> bool:
        """Return True if a relationship has a tag"""
        return tag in self._tags

    def remove_tags(self, *tags: str) -> None:
        """Return True if a relationship has a tag"""
        for tag in tags:
            try:
                self._tags.remove(tag)
            except ValueError:
                # Ignore if the tag is not in the tag set
                pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner,
            "target": self.target,
            "friendship": float(self.friendship),
            "friendship_clamped": self.friendship.clamped,
            "romance": float(self.romance),
            "romance_clamped": self.romance.clamped,
            "tags": list(self._tags),
        }

    def __repr__(self) -> str:
        return "{}(owner={}, target={}, romance={}, friendship={}, tags={})".format(
            self.__class__.__name__,
            self.owner,
            self.target,
            self.romance,
            self.friendship,
            self._tags,
        )


class Relationships(Component):
    """Manages relationship instances between this GameObject and others"""

    __slots__ = "_relationships"

    def __init__(self) -> None:
        super().__init__()
        self._relationships: Dict[int, Relationship] = {}

    def get(self, target: int) -> Relationship:
        """Get an existing or new relationship to the target GameObject"""
        if target not in self._relationships:
            self._relationships[target] = Relationship(self.gameobject.id, target)
        return self._relationships[target]

    def get_all(self) -> List[Relationship]:
        return list(self._relationships.values())

    def get_all_with_tags(self, *tags: str) -> List[Relationship]:
        """
        Get all the relationships between a character and others with specific tags
        """
        return list(
            filter(
                lambda rel: all([rel.has_tag(t) for t in tags]),
                self._relationships.values(),
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.to_dict() for k, v in self._relationships.items()}

    def __getitem__(self, item: int) -> Relationship:
        if item not in self._relationships:
            self._relationships[item] = Relationship(self.gameobject.id, item)
        return self._relationships[item]

    def __contains__(self, item: int) -> bool:
        return item in self._relationships
