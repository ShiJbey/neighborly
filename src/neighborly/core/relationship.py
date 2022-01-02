from typing import Dict, Tuple, List
from enum import IntEnum
from dataclasses import dataclass

CHARGE_MAX: int = 50
CHARGE_MIN: int = -50

SPARK_MAX: int = 50
SPARK_MIN: int = -50

SALIENCE_MAX: int = 100
SALIENCE_MIN: int = 0

friendship_threshold: int = 15
enmity_threshold: int = -10
captivation_threshold: int = 20
like_threshold: int = 20
dislike_threshold: int = -8
hate_threshold: int = -20


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


@dataclass
class RelationshipModifier:
    name: str
    charge: int = 0
    spark: int = 0
    salience: int = 0
    flags: Tuple[int, ...] = ()


class Relationship:

    __slots__ = "_base_salience", "_base_spark", "_base_charge", "_flags", "_modifiers", \
        "_spark", "_charge", "_salience",

    def __init__(self, owner: int, target: int) -> None:
        self._base_salience: int = 0
        self._base_charge: int = 0
        self._base_spark: int = 0
        self._spark: int = 0
        self._charge: int = 0
        self._salience: int = 0
        self._flags: int = 0
        self._modifiers: List[RelationshipModifier] = []

    @property
    def charge(self) -> int:
        return clamp(self._charge, CHARGE_MIN, CHARGE_MAX)

    @property
    def spark(self) -> int:
        return clamp(self._spark, SPARK_MIN, SPARK_MAX)

    @property
    def salience(self) -> int:
        return clamp(self._salience, SALIENCE_MIN, SALIENCE_MAX)

    @property
    def modifiers(self) -> List[RelationshipModifier]:
        return self._modifiers

    def has_flags(self, *flags: int) -> bool:
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
        self._salience += modifier.salience
        self._spark += modifier.spark
        self._charge += modifier.charge
        self.set_flags(*modifier.flags)
        self.modifiers.append(modifier)

    def remove_modifier(self, modifier: RelationshipModifier) -> None:
        self._salience -= modifier.salience
        self._spark -= modifier.spark
        self._charge -= modifier.charge
        self.unset_flags(*modifier.flags)
        self.modifiers.remove(modifier)


_BUILT_IN_MODIFIERS: Dict[str, RelationshipModifier] = {
    "acquaintance": RelationshipModifier(name="acquaintance", flags=(Connection.ACQUAINTANCE,)),
    "friend": RelationshipModifier(name="friend", salience=20, flags=(Connection.FRIEND,)),
    "enemy": RelationshipModifier(name="enemy", salience=20, flags=(Connection.ENEMY,)),
    "best friend": RelationshipModifier(name="best friend", salience=30, flags=(Connection.BEST_FRIEND,)),
    "worst enemy": RelationshipModifier(name="worst enemy", salience=30, flags=(Connection.WORST_ENEMY,)),
    "love interest": RelationshipModifier(name="love interest", salience=30, flags=(Connection.LOVE_INTEREST,)),
    "rival": RelationshipModifier(name="rival", salience=30, flags=(Connection.RIVAL,)),
    "coworker": RelationshipModifier(name="coworker", flags=(Connection.COWORKER,)),
    "significant other": RelationshipModifier(name="significant other", salience=50, flags=(Connection.SIGNIFICANT_OTHER,))
}


def get_modifier(name: str) -> RelationshipModifier:
    return _BUILT_IN_MODIFIERS[name]
