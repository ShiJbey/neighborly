from dataclasses import dataclass
from typing import Dict, ClassVar

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


@dataclass
class RelationshipTag:
    """
    Modifiers attached to Relationship instances that affect
    the development of the relationship over time

    Attributes
    ----------
    name: str
        Name of the tag (used when searching for relationships with
        specific tags
    automatic: bool, default False
        Should this tag automatically apply when the requirements are met
    requirements: List[Callable[['Relationship'], bool]]
        Functions that need to return True for this tag to apply
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
    _tag_registry: ClassVar[Dict[str, 'RelationshipTag']] = {}

    name: str
    automatic: bool = False
    friendship_boost: float = 0
    romance_boost: float = 0
    salience_boost: float = 0
    friendship_increment: float = 0
    romance_increment: float = 0
    salience_increment: float = 0

    @classmethod
    def register_tag(cls, tag: 'RelationshipTag') -> None:
        cls._tag_registry[tag.name] = tag

    @classmethod
    def get_registered_tag(cls, name: str) -> 'RelationshipTag':
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
    _tags: Dict[str, RelationshipTag]
        All the tags active on the Relationship instance
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
        "_tags"
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
        self._tags: Dict[str, RelationshipTag] = {}

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

    def get_tags(self) -> Dict[str, RelationshipTag]:
        return self._tags

    def add_tag(self, tag: str) -> None:
        self._tags[tag] = RelationshipTag.get_registered_tag(tag)
        self._is_dirty = True

    def remove_tag(self, modifier: str) -> None:
        del self._tags[modifier]
        self._is_dirty = True

    def has_tags(self, *names: str) -> bool:
        return all([name in self._tags for name in names])

    def update(self) -> None:
        """Update the relationship when the two characters interact"""
        if self._is_dirty:
            self._recalculate_stats()

        self._salience_base += self._salience_increment
        self._romance_base += self._romance_increment
        self._friendship_base += self._friendship_increment

        self._recalculate_stats()

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
        for modifier in self._tags.values():
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
        return "{}(owner={}, target={}, romance={}, friendship={}, salience={}, tags={})".format(
            self.__class__.__name__,
            self.owner,
            self.target,
            self.romance,
            self.friendship,
            self.salience,
            list(self._tags.keys()),
        )
