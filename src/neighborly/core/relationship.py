"""
relationship.py

Relationships are one of the core factors of a
social simulation next to the chracters. They
track how one character feels about another. And
they evolve as a function of how many times two
characters interact.

Relationships are modeled using three integer values:
- Charge: platonic affinity
- Spark: romantic affinity
- Salience: How mentally relevant is a character to another
"""

from typing import Dict, Tuple, List
from enum import IntEnum
from dataclasses import dataclass

CHARGE_MAX: int = 50
CHARGE_MIN: int = -50

SPARK_MAX: int = 50
SPARK_MIN: int = -50

SALIENCE_MAX: int = 100
SALIENCE_MIN: int = 0

FRIENDSHIP_THRESHOLD: int = 15
ENEMY_THRESHOLD: int = -10
CAPTIVATION_THRESHOLD: int = 20
LIKE_THRESHOLD: int = 20
DISLIKE_THRESHOLD: int = -8
HATE_THRESHOLD: int = -20

SALIENCE_INCREMENT: int = 2


def clamp(value: int, minimum: int, maximum: int) -> int:
    return min(maximum, max(minimum, value))


class Connection(IntEnum):
    FRIEND = 1 << 0
    ENEMY = 1 << 1
    BEST_FRIEND = 1 << 2
    WORST_ENEMY = 1 << 3
    LOVE_INTEREST = 1 << 4
    RIVAL = 1 << 5
    COWORKER = 1 << 6
    ACQUAINTANCE = 1 << 7
    SIGNIFICANT_OTHER = 1 << 8


@dataclass(frozen=True)
class RelationshipModifier:
    name: str
    charge: int = 0
    spark: int = 0
    salience: int = 0
    flags: Tuple[int, ...] = ()


_BUILT_IN_MODIFIERS: Dict[str, RelationshipModifier] = {
    "acquaintance": RelationshipModifier(name="acquaintance", flags=(Connection.ACQUAINTANCE,)),
    "friend": RelationshipModifier(name="friend", salience=20, flags=(Connection.FRIEND,)),
    "enemy": RelationshipModifier(name="enemy", salience=20, flags=(Connection.ENEMY,)),
    "best friend": RelationshipModifier(name="best friend", salience=30, flags=(Connection.BEST_FRIEND, Connection.FRIEND)),
    "worst enemy": RelationshipModifier(name="worst enemy", salience=30, flags=(Connection.WORST_ENEMY, Connection.ENEMY)),
    "love interest": RelationshipModifier(name="love interest", salience=30, flags=(Connection.LOVE_INTEREST,)),
    "rival": RelationshipModifier(name="rival", salience=30, flags=(Connection.RIVAL,)),
    "coworker": RelationshipModifier(name="coworker", flags=(Connection.COWORKER,)),
    "significant other": RelationshipModifier(name="significant other", salience=50, flags=(Connection.SIGNIFICANT_OTHER,)),
    "gender difference": RelationshipModifier(name='different genders', charge=-10),
}


def get_modifier(name: str) -> RelationshipModifier:
    return _BUILT_IN_MODIFIERS[name]


class Relationship:

    __slots__ = "_base_salience", "_spark", "_charge", "_flags", "_modifiers", \
        "_spark_increment", "_charge_increment", "_salience", "_compatibility", \
        "_target", "_owner", "_is_dirty", "_type_modifier", "_compatibility_modifier"

    def __init__(self, owner: int, target: int, compatibility: int, same_gender: bool) -> None:
        self._base_salience: int = 0
        self._charge: int = 0
        self._spark: int = 0
        self._spark_increment: int = 0
        self._charge_increment: int = 0
        self._salience: int = 0
        self._is_dirty: bool = True
        self._flags: int = 0
        self._type_modifier: RelationshipModifier = get_modifier(
            "acquaintance")
        self._compatibility_modifier: RelationshipModifier = RelationshipModifier(
            'compatibility boost', charge=compatibility)
        self._modifiers: List[RelationshipModifier] = []
        self._compatibility: int = compatibility
        self._target: int = target
        self._owner: int = owner

        if not same_gender:
            self.add_modifier(get_modifier("gender difference"))

    @property
    def target(self) -> int:
        return self._target

    @property
    def owner(self) -> int:
        return self._owner

    @property
    def charge(self) -> int:
        if self._is_dirty:
            self._recalculate_stats()
        return self._charge

    @property
    def spark(self) -> int:
        if self._is_dirty:
            self._recalculate_stats()
        return self._spark

    @property
    def salience(self) -> int:
        if self._is_dirty:
            self._recalculate_stats()
        return self._salience

    @property
    def modifiers(self) -> List[RelationshipModifier]:
        return self._modifiers

    def has_flags(self, *flags: int) -> bool:
        if self._is_dirty:
            self._recalculate_stats()

        for flag in flags:
            if self._flags & flag == 0:
                return False
        return True

    def set_flags(self, *flags: int) -> None:
        for flag in flags:
            self._flags |= flag

    def unset_flags(self, *flags: int) -> None:
        for flag in flags:
            self._flags ^= flag

    def add_modifier(self, modifier: RelationshipModifier) -> None:
        self._modifiers.append(modifier)
        self._is_dirty = True

    def remove_modifier(self, modifier: RelationshipModifier) -> None:
        self._modifiers.remove(modifier)
        self._is_dirty = True

    def progress_relationship(self) -> None:
        self._base_salience += SALIENCE_INCREMENT
        self._charge += self._charge_increment
        self._spark += self._spark_increment

        if self.charge > FRIENDSHIP_THRESHOLD:
            self._type_modifier = get_modifier("friend")
            self._is_dirty = True
        elif self.charge < ENEMY_THRESHOLD:
            self._type_modifier = get_modifier("enemy")
            self._is_dirty = True
        if self.spark > CAPTIVATION_THRESHOLD:
            self.add_modifier(get_modifier("love interest"))

    def _recalculate_stats(self) -> None:
        self._spark_increment = 0
        self._charge_increment = 0
        self._salience = self._base_salience
        self._flags = 0

        # Relationship Type modifier
        self._salience += self._type_modifier.salience
        self._spark_increment += self._type_modifier.spark
        self._charge_increment += self._type_modifier.charge
        self.set_flags(*self._type_modifier.flags)

        # Compatibility modifier
        self._salience += self._compatibility_modifier.salience
        self._spark_increment += self._compatibility_modifier.spark
        self._charge_increment += self._compatibility_modifier.charge
        self.set_flags(*self._compatibility_modifier.flags)

        for modifier in self._modifiers:
            self._salience += modifier.salience
            self._spark_increment += modifier.spark
            self._charge_increment += modifier.charge
            self.set_flags(*modifier.flags)

        self._salience = clamp(self._salience, SALIENCE_MIN, SALIENCE_MAX)

        self._is_dirty = False

    def __repr__(self) -> str:
        return "{}(owner={}, target={}, spark={}, charge={}, salience={}, modifiers={})".format(
            self.__class__.__name__,
            self.owner,
            self.target,
            self.spark,
            self.charge,
            self.salience,
            [modifier.name for modifier in self.modifiers]
        )
