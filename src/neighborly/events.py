from __future__ import annotations

from typing import Any, Dict, List

from neighborly.core.ecs import GameObject
from neighborly.core.life_event import LifeEvent
from neighborly.core.roles import Role
from neighborly.core.time import SimDateTime


class JoinSettlementEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        settlement: GameObject,
        character: GameObject,
    ) -> None:
        super().__init__(
            date, [Role("Settlement", settlement), Role("Character", character)]
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
            date, [Role("Settlement", settlement), Role("Character", character)]
        )

    @property
    def settlement(self):
        return self["Settlement"]

    @property
    def character(self):
        return self["Character"]


class DepartEvent(LifeEvent):
    def __init__(
        self, date: SimDateTime, characters: List[GameObject], reason: str
    ) -> None:
        super().__init__(date, [Role("Character", c) for c in characters])
        self.reason = reason

    @property
    def characters(self):
        return self._roles.get_all("Character")

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "reason": self.reason}

    def __str__(self) -> str:
        return f"{super().__str__()}, reason={self.reason}"


class MoveResidenceEvent(LifeEvent):
    def __init__(
        self, date: SimDateTime, residence: GameObject, *characters: GameObject
    ) -> None:
        super().__init__(
            date,
            [Role("Residence", residence), *[Role("Character", c) for c in characters]],
        )

    @property
    def residence(self):
        return self["Residence"]

    @property
    def characters(self):
        return self._roles.get_all("Character")


class BusinessClosedEvent(LifeEvent):
    def __init__(self, date: SimDateTime, business: GameObject) -> None:
        super().__init__(date, [Role("Business", business)])

    @property
    def business(self):
        return self["Business"]


class BirthEvent(LifeEvent):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(date, [Role("Character", character)])

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
                Role("BirthingParent", birthing_parent),
                Role("OtherParent", other_parent),
                Role("Baby", baby),
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
        occupation: str,
    ) -> None:
        super().__init__(
            date, [Role("Character", character), Role("Business", business)]
        )
        self.occupation: str = occupation

    @property
    def character(self):
        return self["Character"]

    @property
    def business(self):
        return self["Business"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "occupation": self.occupation,
        }

    def __str__(self) -> str:
        return "{}, occupation={}".format(
            super().__str__(),
            str(self.occupation),
        )


class EndJobEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: str,
        reason: str,
    ) -> None:
        super().__init__(
            date, [Role("Character", character), Role("Business", business)]
        )
        self.occupation: str = occupation
        self.reason: str = reason

    @property
    def character(self):
        return self["Character"]

    @property
    def business(self):
        return self["Business"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "occupation": self.occupation,
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
        super().__init__(date, [Role("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


class DivorceEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


class StartDatingEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


class BreakUpEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        *characters: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


class StartBusinessEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: str,
    ) -> None:
        super().__init__(
            date, [Role("Character", character), Role("Business", business)]
        )
        self.occupation: str = occupation

    @property
    def character(self):
        return self["Character"]

    @property
    def business(self):
        return self["Business"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "occupation": self.occupation,
        }

    def __str__(self) -> str:
        return "{}, occupation={}".format(super().__str__(), str(self.occupation))


class BusinessOpenEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        business: GameObject,
    ) -> None:
        super().__init__(date, [Role("Business", business)])

    @property
    def business(self):
        return self["Business"]


class NewSettlementEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        settlement: GameObject,
    ) -> None:
        super().__init__(date, [Role("Settlement", settlement)])

    @property
    def settlement(self):
        return self["Settlement"]


class NewCharacterEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", character)])

    @property
    def character(self):
        return self["Character"]


class NewBusinessEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        business: GameObject,
    ) -> None:
        super().__init__(date, [Role("Business", business)])

    @property
    def business(self):
        return self["Business"]


class NewResidenceEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        residence: GameObject,
    ) -> None:
        super().__init__(date, [Role("Residence", residence)])

    @property
    def residence(self):
        return self["Residence"]


class BecomeAdolescentEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", character)])

    @property
    def character(self):
        return self["Character"]


class BecomeYoungAdultEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", character)])

    @property
    def character(self):
        return self["Character"]


class BecomeAdultEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", character)])

    @property
    def character(self):
        return self["Character"]


class BecomeSeniorEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", character)])

    @property
    def character(self):
        return self["Character"]


class RetirementEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: str,
    ) -> None:
        super().__init__(
            date, [Role("Character", character), Role("Business", business)]
        )
        self.occupation: str = occupation

    @property
    def character(self):
        return self["Character"]

    @property
    def business(self):
        return self["Business"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "occupation": self.occupation,
        }


class DeathEvent(LifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
    ) -> None:
        super().__init__(date, [Role("Character", character)])

    @property
    def character(self):
        return self["Character"]
