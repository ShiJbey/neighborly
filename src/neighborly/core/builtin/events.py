from typing import Any, Dict, Tuple

from neighborly.core.character import GameCharacter
from neighborly.core.life_event import (
    EventRoleDatabase,
    EventRoleType,
    LifeEventDatabase,
    LifeEventType,
)
from neighborly.core.relationship import Relationship

EventRoleDatabase.register(
    "Parent", EventRoleType("Parent", components=[GameCharacter])
)

EventRoleDatabase.register("Child", EventRoleType("Child", components=[GameCharacter]))

LifeEventDatabase.register(
    "Child-Birth",
    LifeEventType(
        "Child-Birth",
        [
            EventRoleDatabase["Child"],
            EventRoleDatabase["Parent"],
            EventRoleDatabase["Parent"],
        ],
    ),
)


class ChildBirthEvent(LifeEvent):

    event_type: str = "child-birth"

    __slots__ = "parent_names", "parent_ids", "child_name", "child_id"

    def __init__(
        self,
        timestamp: str,
        parent_names: Tuple[str, str],
        parent_ids: Tuple[int, int],
        child_name: str,
        child_id: int,
    ) -> None:
        super().__init__(timestamp)
        self.parent_names: Tuple[str, str] = parent_names
        self.parent_ids: Tuple[int, int] = parent_ids
        self.child_name: str = child_name
        self.child_id: int = child_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "parent_names": self.parent_names,
            "parent_ids": self.parent_ids,
            "child_name": self.child_name,
            "child_id": self.child_id,
        }

    def __str__(self) -> str:
        return "({}) {} born to parents {} and {}.".format(
            self.timestamp, self.child_name, self.parent_names[0], self.parent_names[1]
        )


class OpenBusinessEvent(LifeEvent):
    event_type: str = "open-business"

    __slots__ = "business_id", "business_name", "owner_id", "owner_name"

    def __init__(
        self,
        timestamp: str,
        business_id: int,
        business_name: str,
        owner_id: int,
        owner_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.business_id: int = business_id
        self.business_name: str = business_name
        self.owner_name: str = owner_name
        self.owner_id: int = owner_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_name": self.business_name,
            "business_id": self.business_id,
            "owner_name": self.owner_name,
            "owner_id": self.owner_id,
        }

    def __str__(self) -> str:
        return "({}) {} opened new business, {}.".format(
            self.timestamp, self.owner_name, self.business_name
        )


class CloseBusinessEvent(LifeEvent):
    event_type: str = "close-business"

    __slots__ = "business_id", "business_name", "owner_id", "owner_name"

    def __init__(
        self,
        timestamp: str,
        business_id: int,
        business_name: str,
        owner_id: int,
        owner_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.business_id: int = business_id
        self.business_name: str = business_name
        self.owner_name: str = owner_name
        self.owner_id: int = owner_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_name": self.business_name,
            "business_id": self.business_id,
            "owner_name": self.owner_name,
            "owner_id": self.owner_id,
        }

    def __str__(self) -> str:
        return "({}) {}'s {} goes out of business.".format(
            self.timestamp, self.owner_name, self.business_name
        )


class DepartureEvent(LifeEvent):
    event_type: str = "departure"

    __slots__ = (
        "character_id",
        "character_name",
    )

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
        }

    def __str__(self) -> str:
        return "({}) {} departed from the town.".format(
            self.timestamp, self.character_name
        )


class MarriageEvent(LifeEvent):
    event_type: str = "marriage"

    __slots__ = (
        "character_ids",
        "character_names",
    )

    def __init__(
        self,
        timestamp: str,
        character_ids: Tuple[int, int],
        character_names: Tuple[str, str],
    ) -> None:
        super().__init__(timestamp)
        self.character_names: Tuple[str, str] = character_names
        self.character_ids: Tuple[int, int] = character_ids

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_names": self.character_names,
            "character_ids": self.character_ids,
        }

    def __str__(self) -> str:
        return "({}) {} and {} got married.".format(
            self.timestamp, self.character_names[0], self.character_names[1]
        )


class DivorceEvent(LifeEvent):
    event_type: str = "marriage"

    __slots__ = (
        "character_ids",
        "character_names",
    )

    def __init__(
        self,
        timestamp: str,
        character_ids: Tuple[int, int],
        character_names: Tuple[str, str],
    ) -> None:
        super().__init__(timestamp)
        self.character_names: Tuple[str, str] = character_names
        self.character_ids: Tuple[int, int] = character_ids

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_names": self.character_names,
            "character_ids": self.character_ids,
        }

    def __str__(self) -> str:
        return "({}) {} and {} got divorced.".format(
            self.timestamp, self.character_names[0], self.character_names[1]
        )


class JobHiringEvent(LifeEvent):
    event_type: str = "job-hiring"

    __slots__ = (
        "business_id",
        "business_name",
        "character_id",
        "character_name",
        "occupation_name",
    )

    def __init__(
        self,
        timestamp: str,
        business_id: int,
        business_name: str,
        character_id: int,
        character_name: str,
        occupation_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.business_id: int = business_id
        self.business_name: str = business_name
        self.character_name: str = character_name
        self.character_id: int = character_id
        self.occupation_name: str = occupation_name

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_name": self.business_name,
            "business_id": self.business_id,
            "character_name": self.character_name,
            "character_id": self.character_id,
            "occupation_name": self.occupation_name,
        }

    def __str__(self) -> str:
        return "({}) {} got hired as a {} at {}.".format(
            self.timestamp,
            self.character_name,
            self.occupation_name,
            self.business_name,
        )


class JobLayoffEvent(LifeEvent):
    event_type: str = "job-layoff"

    __slots__ = (
        "business_id",
        "business_name",
        "character_id",
        "character_name",
        "occupation_name",
    )

    def __init__(
        self,
        timestamp: str,
        business_id: int,
        business_name: str,
        character_id: int,
        character_name: str,
        occupation_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.business_id: int = business_id
        self.business_name: str = business_name
        self.character_name: str = character_name
        self.character_id: int = character_id
        self.occupation_name: str = occupation_name

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_name": self.business_name,
            "business_id": self.business_id,
            "character_name": self.character_name,
            "character_id": self.character_id,
            "occupation_name": self.occupation_name,
        }

    def __str__(self) -> str:
        return "({}) {} got layed-off as a {} at {}.".format(
            self.timestamp,
            self.character_name,
            self.occupation_name,
            self.business_name,
        )


class JobPromotionEvent(LifeEvent):
    event_type: str = "job-promotion"

    __slots__ = (
        "business_id",
        "business_name",
        "character_id",
        "character_name",
        "occupation_name",
    )

    def __init__(
        self,
        timestamp: str,
        business_id: int,
        business_name: str,
        character_id: int,
        character_name: str,
        occupation_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.business_id: int = business_id
        self.business_name: str = business_name
        self.character_name: str = character_name
        self.character_id: int = character_id
        self.occupation_name: str = occupation_name

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_name": self.business_name,
            "business_id": self.business_id,
            "character_name": self.character_name,
            "character_id": self.character_id,
            "occupation_name": self.occupation_name,
        }

    def __str__(self) -> str:
        return "({}) {} got promototed to a {} at {}.".format(
            self.timestamp,
            self.character_name,
            self.occupation_name,
            self.business_name,
        )


class LeaveJobEvent(LifeEvent):
    event_type: str = "leave-job"

    __slots__ = (
        "business_id",
        "business_name",
        "character_id",
        "character_name",
        "occupation_name",
    )

    def __init__(
        self,
        timestamp: str,
        business_id: int,
        business_name: str,
        character_id: int,
        character_name: str,
        occupation_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.business_id: int = business_id
        self.business_name: str = business_name
        self.character_name: str = character_name
        self.character_id: int = character_id
        self.occupation_name: str = occupation_name

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_name": self.business_name,
            "business_id": self.business_id,
            "character_name": self.character_name,
            "character_id": self.character_id,
            "occupation_name": self.occupation_name,
        }

    def __str__(self) -> str:
        return "({}) {} left their job as a {} at {}.".format(
            self.timestamp,
            self.character_name,
            self.occupation_name,
            self.business_name,
        )


class RetirementEvent(LifeEvent):
    event_type: str = "retire"

    __slots__ = (
        "business_id",
        "business_name",
        "character_id",
        "character_name",
        "occupation_name",
    )

    def __init__(
        self,
        timestamp: str,
        business_id: int,
        business_name: str,
        character_id: int,
        character_name: str,
        occupation_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.business_id: int = business_id
        self.business_name: str = business_name
        self.character_name: str = character_name
        self.character_id: int = character_id
        self.occupation_name: str = occupation_name

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "business_name": self.business_name,
            "business_id": self.business_id,
            "character_name": self.character_name,
            "character_id": self.character_id,
            "occupation_name": self.occupation_name,
        }

    def __str__(self) -> str:
        return "({}) {} retired from being a {} at {}.".format(
            self.timestamp,
            self.character_name,
            self.occupation_name,
            self.business_name,
        )


class MoveResidenceEvent(LifeEvent):
    event_type: str = "move-residence"

    __slots__ = ("character_id", "character_name", "residence_id")

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
        residence_id: int,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id
        self.residence_id: int = residence_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
            "residence_id": self.residence_id,
        }

    def __str__(self) -> str:
        return "({}) {} moved to a new residence.".format(
            self.timestamp, self.character_name
        )


class DeathEvent(LifeEvent):
    event_type: str = "death"

    __slots__ = (
        "character_id",
        "character_name",
    )

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
        }

    def __str__(self) -> str:
        return "({}) {} died.".format(self.timestamp, self.character_name)


class DeathInFamilyEvent(LifeEvent):
    event_type: str = "death-in-family"

    __slots__ = (
        "character_id",
        "character_name",
    )

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
        }


class CreateRelationshipEvent(LifeEvent):
    event_type: str = "create-relationship"

    __slots__ = "relationship"

    def __init__(
        self,
        timestamp: str,
        relationship: Relationship,
    ) -> None:
        super().__init__(timestamp)
        self.relationship: Relationship = relationship

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "relationship": self.relationship}


class BecomeAdolescentEvent(LifeEvent):
    event_type: str = "become-teen"

    __slots__ = (
        "character_id",
        "character_name",
    )

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
        }

    def __str__(self) -> str:
        return "({}) {} became an teen.".format(self.timestamp, self.character_name)


class BecomeYoungAdultEvent(LifeEvent):
    event_type: str = "become-young-adult"

    __slots__ = (
        "character_id",
        "character_name",
    )

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
        }

    def __str__(self) -> str:
        return "({}) {} became an young adult.".format(
            self.timestamp, self.character_name
        )


class BecomeAdultEvent(LifeEvent):
    event_type: str = "become-adult"

    __slots__ = (
        "character_id",
        "character_name",
    )

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
        }

    def __str__(self) -> str:
        return "({}) {} became an adult.".format(self.timestamp, self.character_name)


class BecomeElderEvent(LifeEvent):
    event_type: str = "become-elder"

    __slots__ = (
        "character_id",
        "character_name",
    )

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
        }

    def __str__(self) -> str:
        return "({}) {} became an elder.".format(self.timestamp, self.character_name)


class SocializeEvent(LifeEvent):
    event_type: str = "socialize"

    __slots__ = ("character_ids", "character_names", "interaction_type")

    def __init__(
        self,
        timestamp: str,
        character_ids: Tuple[int, int],
        character_names: Tuple[str, str],
        interaction_type: str,
    ) -> None:
        super().__init__(timestamp)
        self.character_names: Tuple[str, str] = character_names
        self.character_ids: Tuple[int, int] = character_ids
        self.interaction_type: str = interaction_type

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_names": self.character_names,
            "character_ids": self.character_ids,
        }

    def __str__(self) -> str:
        return "({}) {} and {} socialized.".format(
            self.timestamp, self.character_names[0], self.character_names[1]
        )


class HomePurchaseEvent(LifeEvent):
    event_type: str = "home-purchase"

    __slots__ = ("character_id", "character_name", "residence_id")

    def __init__(
        self,
        timestamp: str,
        character_id: int,
        character_name: str,
        residence_id: int,
    ) -> None:
        super().__init__(timestamp)
        self.character_name: str = character_name
        self.character_id: int = character_id
        self.residence_id: int = residence_id

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_name": self.character_name,
            "character_id": self.character_id,
            "residence_id": self.residence_id,
        }

    def __str__(self) -> str:
        return "({}) {} purchased a house.".format(self.timestamp, self.character_name)


class BecomeFriendsEvent(LifeEvent):
    """Two characters become friends"""

    event_type: str = "become-friends"

    __slots__ = ("character_ids", "character_names")

    def __init__(
        self,
        timestamp: str,
        character_ids: Tuple[int, int],
        character_names: Tuple[str, str],
    ) -> None:
        super().__init__(timestamp)
        self.character_names: Tuple[str, str] = character_names
        self.character_ids: Tuple[int, int] = character_ids

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_names": self.character_names,
            "character_ids": self.character_ids,
        }

    def __str__(self) -> str:
        return "({}) became friends.".format(self.timestamp, self.character_names)


class BecomeEnemiesEvent(LifeEvent):
    """Two characters become friends"""

    event_type: str = "become-enemies"

    __slots__ = ("character_ids", "character_names")

    def __init__(
        self,
        timestamp: str,
        character_ids: Tuple[int, int],
        character_names: Tuple[str, str],
    ) -> None:
        super().__init__(timestamp)
        self.character_names: Tuple[str, str] = character_names
        self.character_ids: Tuple[int, int] = character_ids

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_names": self.character_names,
            "character_ids": self.character_ids,
        }

    def __str__(self) -> str:
        return "({}) became enemies.".format(self.timestamp, self.character_names)
