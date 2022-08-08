from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag
from typing import Any, ClassVar, Dict, List

from neighborly.core.utils.graph import DirectedGraph

FRIENDSHIP_MAX: float = 50
FRIENDSHIP_MIN: float = -50

ROMANCE_MAX: float = 50
ROMANCE_MIN: float = -50


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a floating point value within a min,max range"""
    return min(maximum, max(minimum, value))


class RelationshipTag(IntFlag):
    """Relationship Tags are bitwise flags that indicate certain relationship types"""

    Acquaintance = 0
    Father = 1 << 0
    Mother = 1 << 1
    Parent = 1 << 2
    Brother = 1 << 3
    Sister = 1 << 4
    Sibling = 1 << 5
    Son = 1 << 6
    Daughter = 1 << 7
    Coworker = 1 << 8
    Boss = 1 << 9
    Spouse = 1 << 10
    Friend = 1 << 11
    Enemy = 1 << 12
    BestFriend = 1 << 13
    WorstEnemy = 1 << 14
    Rival = 1 << 15
    BiologicalFamily = 1 << 16
    Neighbors = 1 << 17
    SignificantOther = 1 << 18
    LoveInterest = 1 << 19
    Child = 1 << 20
    NuclearFamily = 1 << 21


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

    _tag_registry: ClassVar[Dict[str, RelationshipModifier]] = {}

    name: str
    description: str = ""
    friendship_boost: float = 0
    romance_boost: float = 0
    salience_boost: float = 0
    friendship_increment: float = 0
    romance_increment: float = 0
    salience_increment: float = 0

    @classmethod
    def register_tag(cls, tag: RelationshipModifier) -> None:
        """Add a tag to the internal registry for finding later"""
        cls._tag_registry[tag.name] = tag

    @classmethod
    def get_tag(cls, name: str) -> RelationshipModifier:
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
        where a max means best friends and min means worst-enemies
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
    _is_dirty: bool
        Used internally to mark when score need to be recalculated after a change
    _modifiers: Dict[str, RelationshipModifier]
        All the modifiers active on the Relationship instance
    _tags: RelationshipTag
        All the tags that are attached to this
    """

    __slots__ = (
        "_owner",
        "_target",
        "_friendship",
        "_friendship_base",
        "_friendship_increment",
        "_compatibility",
        "_romance",
        "_romance_base",
        "_romance_increment",
        "_is_dirty",
        "_modifiers",
        "_tags",
        "_romance_disabled",
    )

    def __init__(
        self,
        owner: int,
        target: int,
        base_friendship: int = 0,
        base_romance: int = 0,
        tags: RelationshipTag = RelationshipTag.Acquaintance,
        compatibility: float = 0.1,
        romance_disabled: bool = False,
    ) -> None:
        self._owner: int = owner
        self._target: int = target
        self._friendship: float = base_friendship
        self._romance: float = 0
        self._friendship_base: float = 0
        self._romance_base: float = base_romance
        self._is_dirty: bool = True
        self._modifiers: Dict[str, RelationshipModifier] = {}
        self._tags: RelationshipTag = tags
        self._compatibility: float = compatibility
        self._romance_disabled: bool = romance_disabled

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

    def set_compatibility(self, value: float) -> None:
        self._compatibility = value

    def increment_friendship(self, value: float) -> None:
        self._friendship_base += value
        self._is_dirty = True

    def increment_romance(self, value: float) -> None:
        self._romance_base += value
        self._is_dirty = True

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

        self._romance_base += self._romance_increment
        self._friendship_base += self._friendship_increment

        self._recalculate_stats()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner,
            "target": self.target,
            "friendship": self.friendship,
            "romance": self.romance,
            "tags": self._tags,
            "modifiers": [m for m in self._modifiers.keys()],
        }

    def _recalculate_stats(self) -> None:
        """Recalculate all the stats after a change"""
        # Reset the increments
        self._romance_increment = 0.0
        self._friendship_increment = 0.0

        # Reset final values back to base values
        self._friendship = self._friendship_base
        self._romance = self._romance_base

        # Apply modifiers in tags
        for modifier in self._modifiers.values():
            # Apply boosts to relationship scores
            self._romance += modifier.romance_boost
            self._friendship += modifier.friendship_boost
            # Apply increment boosts
            self._romance_increment += modifier.romance_increment
            self._friendship_increment += modifier.friendship_increment

        self._romance = clamp(self._romance, ROMANCE_MIN, ROMANCE_MAX)
        self._friendship = clamp(self._friendship, FRIENDSHIP_MIN, FRIENDSHIP_MAX)

        self._is_dirty = False

    def __repr__(self) -> str:
        return "{}(owner={}, target={}, romance={}, friendship={}, tags={}, modifiers={})".format(
            self.__class__.__name__,
            self.owner,
            self.target,
            self.romance,
            self.friendship,
            self._tags,
            list(self._modifiers.keys()),
        )


class RelationshipGraph(DirectedGraph[Relationship]):
    def __init__(self) -> None:
        super().__init__()

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a new relationship to the graph"""
        self.add_connection(relationship.owner, relationship.target, relationship)

    def get_relationships(self, owner: int) -> List[Relationship]:
        """Get all the outgoing relationships for this character"""
        owner_node = self._nodes[owner]
        return [self._edges[owner, target] for target in owner_node.outgoing]

    def get_all_relationships_with_tags(
        self, owner: int, tags: RelationshipTag
    ) -> List[Relationship]:
        owner_node = self._nodes[owner]

        return list(
            filter(
                lambda rel: rel.has_tags(tags),
                [self._edges[owner, target] for target in owner_node.outgoing],
            )
        )

    def to_dict(self) -> Dict[int, Dict[int, Dict[str, Any]]]:
        network_dict: Dict[int, Dict[int, Dict[str, Any]]] = {}

        for character_id in self._nodes.keys():
            network_dict[character_id] = {}
            for relationship in self.get_relationships(character_id):
                network_dict[character_id][relationship.target] = relationship.to_dict()

        return network_dict
