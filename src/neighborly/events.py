from __future__ import annotations

from typing import Any, Dict, List, Optional

from neighborly.components.character import LifeStageType
from neighborly.core.ecs import Event, GameObject
from neighborly.core.life_event import EventRole, LifeEvent
from neighborly.core.time import SimDateTime


class JoinSettlementEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        settlement: GameObject,
        character: GameObject,
    ) -> None:
        super().__init__(
            date,
            [EventRole("Settlement", settlement), EventRole("Character", character)],
        )

    @property
    def settlement(self):
        return self["Settlement"]

    @property
    def character(self):
        return self["Character"]


class LeaveSettlementEvent(LifeEvent):
    def __init__(
        self, date: SimDateTime, settlement: GameObject, character: GameObject
    ) -> None:
        super().__init__(
            date,
            [EventRole("Settlement", settlement), EventRole("Character", character)],
        )

    @property
    def settlement(self):
        return self["Settlement"]

    @property
    def character(self):
        return self["Character"]


class DepartEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        characters: List[GameObject],
        reason: Optional[LifeEvent] = None,
    ) -> None:
        super().__init__(date, [EventRole("Character", c) for c in characters])
        self.reason = reason

    @property
    def characters(self):
        return self._roles.get_all("Character")

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "reason": self.reason if self.reason else -1}

    def __str__(self) -> str:
        return f"{super().__str__()}, reason={self.reason}"


class MoveResidenceEvent(LifeEvent):
    def __init__(
        self, date: SimDateTime, residence: GameObject, *characters: GameObject
    ) -> None:
        super().__init__(
            date,
            [
                EventRole("Residence", residence),
                *[EventRole("Character", c) for c in characters],
            ],
        )

    @property
    def residence(self):
        return self["Residence"]

    @property
    def characters(self):
        return self._roles.get_all("Character")


class BusinessClosedEvent(LifeEvent):
    def __init__(self, date: SimDateTime, business: GameObject) -> None:
        super().__init__(date, [EventRole("Business", business)])

    @property
    def business(self):
        return self["Business"]


class BirthEvent(LifeEvent):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(date, [EventRole("Character", character)])

    @property
    def character(self):
        return self["Character"]


class GiveBirthEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        birthing_parent: GameObject,
        other_parent: GameObject,
        baby: GameObject,
    ) -> None:
        super().__init__(
            date,
            [
                EventRole("BirthingParent", birthing_parent),
                EventRole("OtherParent", other_parent),
                EventRole("Baby", baby),
            ],
        )

    @property
    def birthing_parent(self):
        return self["BirthingParent"]

    @property
    def other_parent(self):
        return self["OtherParent"]

    @property
    def baby(self):
        return self["Baby"]


class StartJobEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: GameObject,
    ) -> None:
        super().__init__(
            date,
            [
                EventRole("Character", character),
                EventRole("Business", business),
                EventRole("Occupation", occupation),
            ],
        )

    @property
    def character(self):
        return self["Character"]

    @property
    def business(self):
        return self["Business"]

    @property
    def occupation(self):
        return self["occupation"]


class EndJobEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: GameObject,
        reason: LifeEvent,
    ) -> None:
        super().__init__(
            date,
            [
                EventRole("Character", character),
                EventRole("Business", business),
                EventRole("Occupation", occupation),
            ],
        )
        self.reason: LifeEvent = reason

    @property
    def character(self):
        return self["Character"]

    @property
    def business(self):
        return self["Business"]

    @property
    def occupation(self):
        return self["occupation"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "reason": self.reason,
        }

    def __str__(self) -> str:
        return (
            f"{super().__str__()}, "
            f"occupation={self.occupation}, "
            f"reason={self.reason}"
        )


class MarriageEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


class DivorceEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


class StartDatingEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


class BreakUpEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


class StartBusinessEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: GameObject,
    ) -> None:
        super().__init__(
            date,
            [
                EventRole("Character", character),
                EventRole("Business", business),
                EventRole("Occupation", occupation),
            ],
        )

    @property
    def character(self):
        return self["Character"]

    @property
    def business(self):
        return self["Business"]

    @property
    def occupation(self):
        return self["occupation"]


class BusinessOpenEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        business: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Business", business)])

    @property
    def business(self):
        return self["Business"]


class SettlementCreatedEvent(Event):
    __slots__ = "_timestamp", "_settlement"

    _timestamp: SimDateTime
    _settlement: GameObject

    def __init__(
        self,
        date: SimDateTime,
        settlement: GameObject,
    ) -> None:
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
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__()
        self._character = character
        self._timestamp = date

    @property
    def character(self) -> GameObject:
        return self.character

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp


class CharacterNameChangeEvent(Event):
    __slots__ = "_character", "_timestamp", "_first_name", "_last_name"

    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        first_name: str,
        last_name: str,
    ) -> None:
        super().__init__()
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
        date: SimDateTime,
        character: GameObject,
        age: float,
        life_stage: LifeStageType,
    ) -> None:
        super().__init__()
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


class NewBusinessEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        business: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Business", business)])

    @property
    def business(self):
        return self["Business"]


class ResidenceCreatedEvent(Event):
    __slots__ = "_timestamp", "_residence"

    _timestamp: SimDateTime
    """Simulation date when event occurred."""

    _residence: GameObject
    """Reference to the created residence."""

    def __init__(
        self,
        timestamp: SimDateTime,
        residence: GameObject,
    ) -> None:
        super().__init__()
        self._timestamp = timestamp.copy()
        self._residence = residence

    @property
    def residence(self) -> GameObject:
        return self._residence

    @property
    def timestamp(self) -> SimDateTime:
        return self._timestamp


class BecomeAdolescentEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", character)])

    @property
    def character(self):
        return self["Character"]


class BecomeYoungAdultEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", character)])

    @property
    def character(self):
        return self["Character"]


class BecomeAdultEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", character)])

    @property
    def character(self):
        return self["Character"]


class BecomeSeniorEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", character)])

    @property
    def character(self):
        return self["Character"]


class RetirementEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: GameObject,
    ) -> None:
        super().__init__(
            date,
            [
                EventRole("Character", character),
                EventRole("Business", business),
                EventRole("Occupation", occupation),
            ],
        )

    @property
    def character(self):
        return self["Character"]

    @property
    def business(self):
        return self["Business"]

    @property
    def occupation(self):
        return self["Occupation"]


class DeathEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [EventRole("Character", character)])

    @property
    def character(self):
        return self["Character"]
