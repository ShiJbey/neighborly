from __future__ import annotations

from typing import Any, Dict, List

from neighborly.core.ecs import GameObject
from neighborly.core.event import Event, EventRole
from neighborly.core.time import SimDateTime


class DeathEvent(Event):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(
            name="Death",
            timestamp=date.to_iso_str(),
            roles=[
                EventRole("Character", character.id),
            ],
        )


class DepartEvent(Event):
    def __init__(
        self, date: SimDateTime, characters: List[GameObject], reason: str
    ) -> None:
        super().__init__(
            name="Depart",
            timestamp=date.to_iso_str(),
            roles=[EventRole("Character", c.id) for c in characters],
        )
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "reason": self.reason}


class MoveResidenceEvent(Event):
    def __init__(self, date: SimDateTime, *characters: GameObject) -> None:
        super().__init__(
            name="Depart",
            timestamp=date.to_iso_str(),
            roles=[EventRole("Character", c.id) for c in characters],
        )


class BusinessClosedEvent(Event):
    def __init__(self, date: SimDateTime, business: GameObject) -> None:
        super().__init__(
            name="BusinessClosed",
            timestamp=date.to_iso_str(),
            roles=[
                EventRole("Business", business.id),
            ],
        )


class BirthEvent(Event):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(
            name="Birth",
            timestamp=date.to_iso_str(),
            roles=[EventRole("Character", character.id)],
        )


class GiveBirthEvent(Event):
    def __init__(
        self,
        date: SimDateTime,
        birthing_parent: GameObject,
        other_parent: GameObject,
        baby: GameObject,
    ) -> None:
        super().__init__(
            name="GiveBirth",
            timestamp=date.to_iso_str(),
            roles=[
                EventRole("BirthingParent", birthing_parent.id),
                EventRole("OtherParent", other_parent.id),
                EventRole("Baby", baby.id),
            ],
        )


class PregnantEvent(Event):
    def __init__(
        self,
        date: SimDateTime,
        pregnant_one: GameObject,
        partner: GameObject,
    ) -> None:
        super().__init__(
            name="Pregnant",
            timestamp=date.to_iso_str(),
            roles=[
                EventRole("PregnantOne", pregnant_one.id),
                EventRole("Partner", partner.id),
            ],
        )


class RetireEvent(Event):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(
            name="Retire",
            timestamp=date.to_iso_str(),
            roles=[
                EventRole("Character", character.id),
            ],
        )


class EndJobEvent(Event):

    __slots__ = "occupation", "reason"

    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: str,
        reason: str,
    ) -> None:
        super().__init__(
            name="LeaveJob",
            timestamp=date.to_iso_str(),
            roles=[
                EventRole("Business", business.id),
                EventRole("Character", character.id),
            ],
        )
        self.occupation: str = occupation
        self.reason: str = reason

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "reason": self.reason}


class MarriageEvent(Event):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(
            name="Marriage",
            timestamp=date.to_iso_str(),
            roles=[EventRole("Character", c.id) for c in characters],
        )


class DivorceEvent(Event):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(
            name="Divorce",
            timestamp=date.to_iso_str(),
            roles=[EventRole("Character", c.id) for c in characters],
        )
