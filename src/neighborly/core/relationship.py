from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag, auto
from typing import Any, ClassVar, Dict, List, Optional

from neighborly.core.ecs import Component, World

FRIENDSHIP_MAX: float = 50
FRIENDSHIP_MIN: float = -50

ROMANCE_MAX: float = 50
ROMANCE_MIN: float = -50

SALIENCE_MAX: float = 100
SALIENCE_MIN: float = 0
SALIENCE_INCREMENT: float = 1


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a floating point value within a min,max range"""
    return min(maximum, max(minimum, value))


class RelationshipTag(IntFlag):
    """Relationship Tags are bitwise flags that indicate certain relationship types"""

    NONE = 0
    Father = auto()
    Mother = auto()
    Parent = auto()
    Brother = auto()
    Sister = auto()
    Sibling = auto()
    Son = auto()
    Daughter = auto()
    Coworker = auto()
    Boss = auto()
    Spouse = auto()
    Friend = auto()
    Enemy = auto()
    BestFriend = auto()
    WorstEnemy = auto()
    Rival = auto()
    Acquaintance = auto()
    BiologicalFamily = auto()
    Neighbors = auto()
    SignificantOther = auto()
    LoveInterest = auto()


@dataclass
class RelationshipModifier:
    """
    Modifiers apply buffs to the friendship, romance, and salience
    stats on relationship instances

    Attributes
    ----------
    name: str
        Name of the tag (used when searching for relationships with
        specific tags)
    description: str
        String description of what this relationship modifier means
    friendship_boost: float, default 0
        Flat value to apply the friendship value by
    romance_boost: float, default 0
        Flat value to apply the romance value
    salience_boost: float, default 0
        Flat value to apply to the salience value
    friendship_increment: float, default 0
        Flat value to apply when incrementing the friendship value
    romance_increment: float, default 0
        Flat value to apply when incrementing the romance value
    salience_increment: float, default 0
        Flat value to apply when incrementing the salience value
    """

    _tag_registry: ClassVar[Dict[str, "RelationshipModifier"]] = {}

    name: str
    description: str = ""
    friendship_boost: float = 0
    romance_boost: float = 0
    salience_boost: float = 0
    friendship_increment: float = 0
    romance_increment: float = 0
    salience_increment: float = 0

    @classmethod
    def register_tag(cls, tag: "RelationshipModifier") -> None:
        """Add a tag to the internal registry for finding later"""
        cls._tag_registry[tag.name] = tag

    @classmethod
    def get_tag(cls, name: str) -> "RelationshipModifier":
        """Retrieve a tag from the internal registry of RelationshipModifiers"""
        return cls._tag_registry[name]


class Relationship:
    """
    Relationships are one of the core factors of a
    social simulation next to the characters. They
    track how one character feels about another. And
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
        The character who this relationship is directed toward
    _friendship: float
        Friendship score on the scale [FRIENDSHIP_MIN, FRIENDSHIP_MAX]
        where a max is best friends and the min is worst enemies
    _friendship_base: float
        Friendship score without any modifiers from tags
    _friendship_increment: float
        Amount to increment the friendship score by after each interaction
    _romance: float
        Romance score on the scale [ROMANCE_MIN, ROMANCE_MAX]
        where a max is complete infatuation and the min is repulsion
    _romance_base: float
        Romance score without any modifiers from tags
    _romance_increment: float
        Amount to increment the romance score by after each interaction
    _salience: float
        Salience score on the scale [SALIENCE_MIN, SALIENCE_MAX]
        where a max is I know them well and the min is "I've never seen this
        person in my life"
    _salience_base: float
        Salience score without any modifiers from tags
    _salience_increment: float
        Amount to increment the salience score by after each interaction
    _is_dirty: bool
        Used internally to mark when score need to be recalculated after a change
    _modifiers: Dict[str, RelationshipModifier]
        All the modifiers active on the Relationship instance
    _tags: RelationshipTag
        All the tags that that are attached to this
    """

    __slots__ = (
        "_owner",
        "_target",
        "_friendship",
        "_friendship_base",
        "_friendship_increment",
        "_romance",
        "_romance_base",
        "_romance_increment",
        "_salience",
        "_salience_base",
        "_salience_increment",
        "_is_dirty",
        "_modifiers",
        "_tags",
    )

    def __init__(
        self,
        owner: int,
        target: int,
    ) -> None:
        self._owner: int = owner
        self._target: int = target
        self._friendship: float = 0
        self._romance: float = 0
        self._salience: float = 0
        self._friendship_base: float = 0
        self._romance_base: float = 0
        self._salience_base: float = 0
        self._friendship_increment: float = 0
        self._romance_increment: float = 0
        self._salience_increment: float = 0
        self._is_dirty: bool = True
        self._modifiers: Dict[str, RelationshipModifier] = {}
        self._tags: RelationshipTag = RelationshipTag.NONE

    @property
    def target(self) -> int:
        return self._target

    @property
    def owner(self) -> int:
        return self._owner

    @property
    def friendship(self) -> float:
        if self._is_dirty:
            self._recalculate_stats()
        return self._friendship

    @property
    def romance(self) -> float:
        if self._is_dirty:
            self._recalculate_stats()
        return self._romance

    @property
    def salience(self) -> float:
        if self._is_dirty:
            self._recalculate_stats()
        return self._salience

    def add_tags(self, tags: RelationshipTag) -> None:
        """Return add a tag to this Relationship"""
        self._tags |= tags

    def has_tags(self, tags: RelationshipTag) -> bool:
        """Return True if a relationship has a tag"""
        return bool(self._tags & tags)

    def remove_tags(self, tags: RelationshipTag) -> None:
        """Return True if a relationship has a tag"""
        self._tags = self._tags & (~tags)

    def get_modifiers(self) -> List[RelationshipModifier]:
        """Return a list of the modifiers attached to this Relationship instance"""
        return list(self._modifiers.values())

    def has_modifier(self, name: str) -> bool:
        """Return true if the relationship has a modifier with the given name"""
        return name in self._modifiers

    def add_modifier(self, modifier: RelationshipModifier) -> None:
        """Add a RelationshipModifier to the relationship instance"""
        self._modifiers[modifier.name] = modifier
        self._is_dirty = True

    def remove_modifier(self, name: str) -> None:
        """Remove modifier with the given name"""
        del self._modifiers[name]
        self._is_dirty = True

    def update(self) -> None:
        """Update the relationship when the two characters interact"""
        if self._is_dirty:
            self._recalculate_stats()

        self._salience_base += self._salience_increment
        self._romance_base += self._romance_increment
        self._friendship_base += self._friendship_increment

        self._recalculate_stats()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner,
            "target": self.target,
            "friendship": self.friendship,
            "romance": self.romance,
            "salience": self.salience,
            "tags": self._tags,
            "modifiers": [m for m in self._modifiers.keys()],
        }

    def _recalculate_stats(self) -> None:
        """Recalculate all the stats after a change"""
        # Reset the increments
        self._romance_increment = 0.0
        self._friendship_increment = 0.0
        self._salience_increment = SALIENCE_INCREMENT

        # Reset final values back to base values
        self._friendship = self._friendship_base
        self._romance = self._romance_base
        self._salience = self._salience_base

        # Apply modifiers in tags
        for modifier in self._modifiers.values():
            # Apply boosts to relationship scores
            self._salience += modifier.salience_boost
            self._romance += modifier.romance_boost
            self._friendship += modifier.friendship_boost
            # Apply increment boosts
            self._romance_increment += modifier.romance_increment
            self._salience_increment += modifier.salience_increment
            self._friendship_increment += modifier.friendship_increment

        self._salience = clamp(self._salience, SALIENCE_MIN, SALIENCE_MAX)
        self._romance = clamp(self._romance, ROMANCE_MIN, ROMANCE_MAX)
        self._friendship = clamp(self._friendship, FRIENDSHIP_MIN, FRIENDSHIP_MAX)

        self._is_dirty = False

    def __repr__(self) -> str:
        return "{}(owner={}, target={}, romance={}, friendship={}, salience={}, tags={}, modifiers={})".format(
            self.__class__.__name__,
            self.owner,
            self.target,
            self.romance,
            self.friendship,
            self.salience,
            self._tags,
            list(self._modifiers.keys()),
        )


class DuplicateRelationshipError(Exception):
    """Raise error when attempting to create a second relationship to a character"""

    def __init__(self, character: int, target: int) -> None:
        super().__init__()
        self.message = f"Relationship already exist for {character} to {target}"

    def __str__(self) -> str:
        return self.message


class RelationshipManager(Component):
    """Manages the relationships from a specific character to others"""

    __slots__ = "_relationships"

    def __init__(self) -> None:
        super().__init__()
        self._relationships: Dict[int, Relationship] = {}

    def add_relationship(self, relationship: Relationship) -> None:
        if relationship.target in self._relationships:
            raise DuplicateRelationshipError(self.gameobject.id, relationship.target)

        self._relationships[relationship.target] = relationship

    def get_relationship(self, target: int) -> Optional[Relationship]:
        return self._relationships.get(target)

    def remove_relationship(self, target: int) -> None:
        del self._relationships[target]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "relationships": [r.to_dict() for r in self._relationships.values()],
        }

    @classmethod
    def create(cls, world: World, **kwargs) -> RelationshipManager:
        return cls()
