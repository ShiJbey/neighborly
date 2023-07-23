from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple, Type

from neighborly.components.business import Occupation
from neighborly.components.character import LifeStageType
from neighborly.core.ecs import Event, GameObject, World
from neighborly.core.life_event import LifeEvent
from neighborly.core.time import SimDateTime


class JoinSettlementEvent(LifeEvent):
    __slots__ = "settlement", "character"

    settlement: GameObject
    """The settlement joined."""

    character: GameObject
    """The character that joined the settlement."""

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        settlement: GameObject,
        character: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        self.settlement = settlement
        self.character = character

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "settlement": self.settlement.uid,
            "character": self.character.uid,
        }

    def __str__(self) -> str:
        return "{} [@ {}] '{}' joined the '{}' settlement".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
            self.settlement.name,
        )

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.settlement, self.character]


class LeaveSettlementEvent(LifeEvent):
    __slots__ = "settlement", "character"

    settlement: GameObject
    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        settlement: GameObject,
        character: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        self.settlement = settlement
        self.character = character

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "settlement": self.settlement,
            "character": self.character,
        }

    def __str__(self) -> str:
        return "{} [@ {}] '{}' left the '{}' settlement.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
            self.settlement.name,
        )

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.settlement, self.character]


class DepartEvent(LifeEvent):
    __slots__ = "characters", "reason", "settlement"

    characters: Tuple[GameObject, ...]
    reason: Optional[LifeEvent]
    settlement: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        characters: List[GameObject],
        settlement: GameObject,
        reason: Optional[LifeEvent] = None,
    ) -> None:
        super().__init__(world, date)
        self.characters = tuple(characters)
        self.reason = reason
        self.settlement = settlement

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "characters": [c.uid for c in self.characters],
            "reason": self.reason.event_id if self.reason else -1,
        }

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return list(self.characters)

    def __str__(self) -> str:
        if self.reason:
            return "{} [@ {}] '{}' departed from '{}' because of '{}'".format(
                type(self).__name__,
                str(self.timestamp),
                " and ".join([c.name for c in self.characters]),
                self.settlement.name,
                type(self.reason).__name__,
            )
        else:
            return "{} [@ {}] '{}' departed from '{}'".format(
                type(self).__name__,
                str(self.timestamp),
                " and ".join([c.name for c in self.characters]),
                self.settlement.name,
            )


class MoveResidenceEvent(LifeEvent):
    __slots__ = "residence", "characters"

    residence: GameObject
    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        residence: GameObject,
        *characters: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        self.residence = residence
        self.characters = characters

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "residence": self.residence.uid,
            "characters": [c.uid for c in self.characters],
        }

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return list(self.characters)

    def __str__(self) -> str:
        return "{} [@ {}] '{}' moved into a new residence ({}).".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
            self.residence.name,
        )


class BusinessClosedEvent(LifeEvent):
    __slots__ = "business"

    business: GameObject

    def __init__(self, world: World, date: SimDateTime, business: GameObject) -> None:
        super().__init__(world, date)
        self.business = business

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.business]

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "business": self.business}

    def __str__(self) -> str:
        return "{} [@ {}] {} closed for business".format(
            type(self).__name__,
            str(self.timestamp),
            self.business.name,
        )


class BirthEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(self, world: World, date: SimDateTime, character: GameObject) -> None:
        super().__init__(world, date)
        self.character = character

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}


class HaveChildEvent(LifeEvent):
    __slots__ = "birthing_parent", "other_parent", "baby"

    birthing_parent: GameObject
    other_parent: GameObject
    baby: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        birthing_parent: GameObject,
        other_parent: GameObject,
        baby: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        self.birthing_parent = birthing_parent
        self.other_parent = other_parent
        self.baby = baby

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.birthing_parent, self.other_parent, self.baby]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "birthing_parent": self.birthing_parent,
            "other_parent": self.other_parent,
            "baby": self.baby,
        }


class StartJobEvent(LifeEvent):
    __slots__ = "character", "business", "occupation"

    character: GameObject
    business: business
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

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.business, self.character]

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

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

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


class MarriageEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return list(self.characters)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} got married.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class DivorceEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return list(self.characters)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} got divorced.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class StartDatingEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return list(self.characters)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} started dating.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class BreakUpEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return list(self.characters)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} broke up.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
        )


class BecameAcquaintancesEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return list(self.characters)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}

    def __str__(self) -> str:
        return "{} [@ {}] {} became a acquaintances.".format(
            type(self).__name__,
            str(self.timestamp),
            " and ".join([c.name for c in self.characters]),
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

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.business, self.character]

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


class SettlementCreatedEvent(Event):
    __slots__ = "_timestamp", "_settlement"

    _timestamp: SimDateTime
    _settlement: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        settlement: GameObject,
    ) -> None:
        super().__init__(world)
        self._timestamp = date.copy()
        self._settlement = settlement

    @property
    def settlement(self) -> GameObject:
        return self._settlement

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp


class CharacterCreatedEvent(Event):
    __slots__ = "_character", "_timestamp"

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world)
        self._character = character
        self._timestamp = date

    @property
    def character(self) -> GameObject:
        return self.character

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp


class RelationshipCreatedEvent(Event):
    __slots__ = "_relationship", "_owner", "_target"

    def __init__(
        self,
        relationship: GameObject,
        owner: GameObject,
        target: GameObject
    ) -> None:
        super().__init__(world=relationship.world)
        self._relationship = relationship
        self._owner = owner
        self._target = target

    @property
    def relationship(self) -> GameObject:
        return self._relationship

    @property
    def owner(self) -> GameObject:
        return self._owner

    @property
    def target(self) -> GameObject:
        return self._target


class CharacterNameChangeEvent(Event):
    __slots__ = "_character", "_timestamp", "_first_name", "_last_name"

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
        first_name: str,
        last_name: str,
    ) -> None:
        super().__init__(world)
        self._character = character
        self._timestamp = date
        self._first_name = first_name
        self._last_name = last_name

    @property
    def character(self) -> GameObject:
        return self.character

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp

    @property
    def first_name(self) -> str:
        return self._first_name

    @property
    def last_name(self) -> str:
        return self._last_name


class CharacterAgeChangeEvent(Event):
    __slots__ = "_character", "_timestamp", "_age", "_life_stage"

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
        age: float,
        life_stage: LifeStageType,
    ) -> None:
        super().__init__(world)
        self._character = character
        self._timestamp = date
        self._age = age
        self._life_stage = life_stage

    @property
    def character(self) -> GameObject:
        return self.character

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp

    @property
    def age(self) -> float:
        return self._age

    @property
    def life_stage(self) -> LifeStageType:
        return self._life_stage


class NewBusinessEvent(Event):
    __slots__ = "business"

    business: GameObject

    def __init__(
        self,
        world: World,
        business: GameObject,
    ) -> None:
        super().__init__(world)
        self.business = business


class ResidenceCreatedEvent(Event):
    __slots__ = "_timestamp", "_residence"

    _timestamp: SimDateTime
    """Simulation date when event occurred."""

    _residence: GameObject
    """Reference to the created residence."""

    def __init__(
        self,
        world: World,
        timestamp: SimDateTime,
        residence: GameObject,
    ) -> None:
        super().__init__(world)
        self._timestamp = timestamp.copy()
        self._residence = residence

    @property
    def residence(self) -> GameObject:
        return self._residence

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp


class BecomeAdolescentEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} became a adolescent.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class BecomeYoungAdultEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} became a young adult.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class BecomeAdultEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} became an adult.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class BecomeSeniorEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} became a senior.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
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

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

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


class DeathEvent(LifeEvent):
    __slots__ = "character"

    character: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.character = character

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.character]

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "character": self.character}

    def __str__(self) -> str:
        return "{} [@ {}] {} died.".format(
            type(self).__name__,
            str(self.timestamp),
            self.character.name,
        )


class GetPregnantEvent(LifeEvent):
    __slots__ = "pregnant_one", "partner"

    pregnant_one: GameObject
    """The character that got pregnant."""

    partner: GameObject
    """The character that impregnated the other."""

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        pregnant_one: GameObject,
        partner: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
        )
        self.pregnant_one = pregnant_one
        self.partner = partner

    def get_affected_gameobjects(self) -> Iterable[GameObject]:
        return [self.pregnant_one]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "pregnant_one": self.pregnant_one.uid,
            "partner": self.partner.uid,
        }

    def __str__(self) -> str:
        return "{} [@ {}] {} got pregnant by {}.".format(
            type(self).__name__,
            str(self.timestamp),
            self.pregnant_one.name,
            self.partner.name,
        )
