from __future__ import annotations

from typing import List

from neighborly.builtin.helpers import is_single
from neighborly.builtin.statuses import (
    Adult,
    Dating,
    Elder,
    Married,
    Pregnant,
    Retired,
    Unemployed,
)
from neighborly.core.business import Business, Occupation, OccupationType
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import (
    EventRoles,
    EventRoleType,
    LifeEvent,
    LifeEventType,
    join_filters,
)
from neighborly.core.relationship import RelationshipGraph, RelationshipTag
from neighborly.core.time import SimDateTime


def single_person_role_type() -> EventRoleType:
    def can_get_married(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)
        if len(
            rel_graph.get_all_relationships_with_tags(
                gameobject.id, RelationshipTag.SignificantOther
            )
        ):
            return False
        return True

    return EventRoleType(
        "SinglePerson", [GameCharacter, Adult], filter_fn=can_get_married
    )


def potential_spouse_role() -> EventRoleType:
    def filter_fn(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)
        is_single = (
            len(
                rel_graph.get_all_relationships_with_tags(
                    gameobject.id, RelationshipTag.SignificantOther
                )
            )
            == 0
        )

        if not rel_graph.has_connection(gameobject.id, event["SinglePerson"]):
            return False

        in_love = (
            rel_graph.get_connection(gameobject.id, event["SinglePerson"]).romance > 45
        )
        return is_single and in_love

    return EventRoleType("PotentialSpouse", [GameCharacter, Adult], filter_fn=filter_fn)


def hiring_business_role() -> EventRoleType:
    """Defines a Role for a business with job opening"""

    def help_wanted(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        business = gameobject.get_component(Business)
        return len(business.get_open_positions()) > 0

    return EventRoleType("HiringBusiness", components=[Business], filter_fn=help_wanted)


def unemployed_role() -> EventRoleType:
    """Defines event Role for a character without a job"""
    return EventRoleType("Unemployed", components=[Unemployed])


def hire_employee_event() -> LifeEventType:
    def cb(world: World, event: LifeEvent):
        engine = world.get_resource(NeighborlyEngine)
        character = world.get_gameobject(event["Unemployed"]).get_component(
            GameCharacter
        )
        business = world.get_gameobject(event["HiringBusiness"]).get_component(Business)

        position = engine.rng.choice(business.get_open_positions())

        character.gameobject.remove_component(Unemployed)

        business.add_employee(character.gameobject.id, position)
        character.gameobject.add_component(
            Occupation(
                OccupationTypeLibrary.get(position),
                business.gameobject.id,
            )
        )

    return LifeEventType(
        "HiredAtBusiness",
        roles=[EventRoles.get("HiringBusiness"), EventRoles.get("Unemployed")],
        execute_fn=cb,
    )


# class ChildBirthEvent(LifeEvent):
#     event_type: str = "child-birth"
#
#     __slots__ = "parent_names", "parent_ids", "child_name", "child_id"
#
#     def __init__(
#         self,
#         timestamp: str,
#         parent_names: Tuple[str, str],
#         parent_ids: Tuple[int, int],
#         child_name: str,
#         child_id: int,
#     ) -> None:
#         super().__init__(timestamp)
#         self.parent_names: Tuple[str, str] = parent_names
#         self.parent_ids: Tuple[int, int] = parent_ids
#         self.child_name: str = child_name
#         self.child_id: int = child_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "parent_names": self.parent_names,
#             "parent_ids": self.parent_ids,
#             "child_name": self.child_name,
#             "child_id": self.child_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} born to parents {} and {}.".format(
#             self.timestamp, self.child_name, self.parent_names[0], self.parent_names[1]
#         )
#
#
# class OpenBusinessEvent(LifeEvent):
#     event_type: str = "open-business"
#
#     __slots__ = "business_id", "business_name", "owner_id", "owner_name"
#
#     def __init__(
#         self,
#         timestamp: str,
#         business_id: int,
#         business_name: str,
#         owner_id: int,
#         owner_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.business_id: int = business_id
#         self.business_name: str = business_name
#         self.owner_name: str = owner_name
#         self.owner_id: int = owner_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "business_name": self.business_name,
#             "business_id": self.business_id,
#             "owner_name": self.owner_name,
#             "owner_id": self.owner_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} opened new business, {}.".format(
#             self.timestamp, self.owner_name, self.business_name
#         )
#
#
# class CloseBusinessEvent(LifeEvent):
#     event_type: str = "close-business"
#
#     __slots__ = "business_id", "business_name", "owner_id", "owner_name"
#
#     def __init__(
#         self,
#         timestamp: str,
#         business_id: int,
#         business_name: str,
#         owner_id: int,
#         owner_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.business_id: int = business_id
#         self.business_name: str = business_name
#         self.owner_name: str = owner_name
#         self.owner_id: int = owner_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "business_name": self.business_name,
#             "business_id": self.business_id,
#             "owner_name": self.owner_name,
#             "owner_id": self.owner_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {}'s {} goes out of business.".format(
#             self.timestamp, self.owner_name, self.business_name
#         )
#
#
# class DepartureEvent(LifeEvent):
#     event_type: str = "departure"
#
#     __slots__ = (
#         "character_id",
#         "character_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} departed from the town.".format(
#             self.timestamp, self.character_name
#         )
#
#
# class MarriageEvent(LifeEvent):
#     event_type: str = "marriage"
#
#     __slots__ = (
#         "character_ids",
#         "character_names",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_ids: Tuple[int, int],
#         character_names: Tuple[str, str],
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_names: Tuple[str, str] = character_names
#         self.character_ids: Tuple[int, int] = character_ids
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_names": self.character_names,
#             "character_ids": self.character_ids,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} and {} got married.".format(
#             self.timestamp, self.character_names[0], self.character_names[1]
#         )
#
#
# class DivorceEvent(LifeEvent):
#     event_type: str = "marriage"
#
#     __slots__ = (
#         "character_ids",
#         "character_names",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_ids: Tuple[int, int],
#         character_names: Tuple[str, str],
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_names: Tuple[str, str] = character_names
#         self.character_ids: Tuple[int, int] = character_ids
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_names": self.character_names,
#             "character_ids": self.character_ids,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} and {} got divorced.".format(
#             self.timestamp, self.character_names[0], self.character_names[1]
#         )
#
#
# class JobHiringEvent(LifeEvent):
#     event_type: str = "job-hiring"
#
#     __slots__ = (
#         "business_id",
#         "business_name",
#         "character_id",
#         "character_name",
#         "occupation_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         business_id: int,
#         business_name: str,
#         character_id: int,
#         character_name: str,
#         occupation_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.business_id: int = business_id
#         self.business_name: str = business_name
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#         self.occupation_name: str = occupation_name
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "business_name": self.business_name,
#             "business_id": self.business_id,
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#             "occupation_name": self.occupation_name,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} got hired as a {} at {}.".format(
#             self.timestamp,
#             self.character_name,
#             self.occupation_name,
#             self.business_name,
#         )
#
#
# class JobLayoffEvent(LifeEvent):
#     event_type: str = "job-layoff"
#
#     __slots__ = (
#         "business_id",
#         "business_name",
#         "character_id",
#         "character_name",
#         "occupation_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         business_id: int,
#         business_name: str,
#         character_id: int,
#         character_name: str,
#         occupation_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.business_id: int = business_id
#         self.business_name: str = business_name
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#         self.occupation_name: str = occupation_name
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "business_name": self.business_name,
#             "business_id": self.business_id,
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#             "occupation_name": self.occupation_name,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} got laid-off as a {} at {}.".format(
#             self.timestamp,
#             self.character_name,
#             self.occupation_name,
#             self.business_name,
#         )
#
#
# class JobPromotionEvent(LifeEvent):
#     event_type: str = "job-promotion"
#
#     __slots__ = (
#         "business_id",
#         "business_name",
#         "character_id",
#         "character_name",
#         "occupation_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         business_id: int,
#         business_name: str,
#         character_id: int,
#         character_name: str,
#         occupation_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.business_id: int = business_id
#         self.business_name: str = business_name
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#         self.occupation_name: str = occupation_name
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "business_name": self.business_name,
#             "business_id": self.business_id,
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#             "occupation_name": self.occupation_name,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} got promoted to a {} at {}.".format(
#             self.timestamp,
#             self.character_name,
#             self.occupation_name,
#             self.business_name,
#         )
#
#
# class LeaveJobEvent(LifeEvent):
#     event_type: str = "leave-job"
#
#     __slots__ = (
#         "business_id",
#         "business_name",
#         "character_id",
#         "character_name",
#         "occupation_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         business_id: int,
#         business_name: str,
#         character_id: int,
#         character_name: str,
#         occupation_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.business_id: int = business_id
#         self.business_name: str = business_name
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#         self.occupation_name: str = occupation_name
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "business_name": self.business_name,
#             "business_id": self.business_id,
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#             "occupation_name": self.occupation_name,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} left their job as a {} at {}.".format(
#             self.timestamp,
#             self.character_name,
#             self.occupation_name,
#             self.business_name,
#         )
#
#
# class RetirementEvent(LifeEvent):
#     event_type: str = "retire"
#
#     __slots__ = (
#         "business_id",
#         "business_name",
#         "character_id",
#         "character_name",
#         "occupation_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         business_id: int,
#         business_name: str,
#         character_id: int,
#         character_name: str,
#         occupation_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.business_id: int = business_id
#         self.business_name: str = business_name
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#         self.occupation_name: str = occupation_name
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "business_name": self.business_name,
#             "business_id": self.business_id,
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#             "occupation_name": self.occupation_name,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} retired from being a {} at {}.".format(
#             self.timestamp,
#             self.character_name,
#             self.occupation_name,
#             self.business_name,
#         )
#
#
# class MoveResidenceEvent(LifeEvent):
#     event_type: str = "move-residence"
#
#     __slots__ = ("character_id", "character_name", "residence_id")
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#         residence_id: int,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#         self.residence_id: int = residence_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#             "residence_id": self.residence_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} moved to a new residence.".format(
#             self.timestamp, self.character_name
#         )
#
#
# class DeathEvent(LifeEvent):
#     event_type: str = "death"
#
#     __slots__ = (
#         "character_id",
#         "character_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} died.".format(self.timestamp, self.character_name)
#
#
# class DeathInFamilyEvent(LifeEvent):
#     event_type: str = "death-in-family"
#
#     __slots__ = (
#         "character_id",
#         "character_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#         }
#

#
# class BecomeAdolescentEvent(LifeEvent):
#     event_type: str = "become-teen"
#
#     __slots__ = (
#         "character_id",
#         "character_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} became an teen.".format(self.timestamp, self.character_name)
#
#
# class BecomeYoungAdultEvent(LifeEvent):
#     event_type: str = "become-young-adult"
#
#     __slots__ = (
#         "character_id",
#         "character_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} became an young adult.".format(
#             self.timestamp, self.character_name
#         )
#
#
# class BecomeAdultEvent(LifeEvent):
#     event_type: str = "become-adult"
#
#     __slots__ = (
#         "character_id",
#         "character_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} became an adult.".format(self.timestamp, self.character_name)
#
#
# class BecomeElderEvent(LifeEvent):
#     event_type: str = "become-elder"
#
#     __slots__ = (
#         "character_id",
#         "character_name",
#     )
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} became an elder.".format(self.timestamp, self.character_name)
#
#
# class SocializeEvent(LifeEvent):
#     event_type: str = "socialize"
#
#     __slots__ = ("character_ids", "character_names", "interaction_type")
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_ids: Tuple[int, int],
#         character_names: Tuple[str, str],
#         interaction_type: str,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_names: Tuple[str, str] = character_names
#         self.character_ids: Tuple[int, int] = character_ids
#         self.interaction_type: str = interaction_type
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_names": self.character_names,
#             "character_ids": self.character_ids,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} and {} socialized.".format(
#             self.timestamp, self.character_names[0], self.character_names[1]
#         )
#
#
# class HomePurchaseEvent(LifeEvent):
#     event_type: str = "home-purchase"
#
#     __slots__ = ("character_id", "character_name", "residence_id")
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_id: int,
#         character_name: str,
#         residence_id: int,
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_name: str = character_name
#         self.character_id: int = character_id
#         self.residence_id: int = residence_id
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_name": self.character_name,
#             "character_id": self.character_id,
#             "residence_id": self.residence_id,
#         }
#
#     def __str__(self) -> str:
#         return "({}) {} purchased a house.".format(self.timestamp, self.character_name)
#
#
# class BecomeFriendsEvent(LifeEvent):
#     """Two characters become friends"""
#
#     event_type: str = "become-friends"
#
#     __slots__ = ("character_ids", "character_names")
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_ids: Tuple[int, int],
#         character_names: Tuple[str, str],
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_names: Tuple[str, str] = character_names
#         self.character_ids: Tuple[int, int] = character_ids
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_names": self.character_names,
#             "character_ids": self.character_ids,
#         }
#
#     def __str__(self) -> str:
#         return "({}) became friends.".format(self.timestamp, self.character_names)
#
#
# class BecomeEnemiesEvent(LifeEvent):
#     """Two characters become friends"""
#
#     event_type: str = "become-enemies"
#
#     __slots__ = ("character_ids", "character_names")
#
#     def __init__(
#         self,
#         timestamp: str,
#         character_ids: Tuple[int, int],
#         character_names: Tuple[str, str],
#     ) -> None:
#         super().__init__(timestamp)
#         self.character_names: Tuple[str, str] = character_names
#         self.character_ids: Tuple[int, int] = character_ids
#
#     @classmethod
#     def get_type(cls) -> str:
#         return cls.event_type
#
#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             **super().to_dict(),
#             "character_names": self.character_names,
#             "character_ids": self.character_ids,
#         }
#
#     def __str__(self) -> str:
#         return "({}) became enemies.".format(self.timestamp, self.character_names)
def become_friends_event(
    threshold: int = 25, probability: float = 1.0
) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def bind_potential_friend(world: World, event: LifeEvent):
        """
        Return a Character that has a mutual friendship score
        with PersonA that is above a given threshold
        """
        rel_graph = world.get_resource(RelationshipGraph)
        engine = world.get_resource(NeighborlyEngine)
        person_a_relationships = rel_graph.get_relationships(event["PersonA"])
        eligible_characters: List[GameObject] = []
        for rel in person_a_relationships:
            if (
                world.has_gameobject(rel.target)
                and rel_graph.has_connection(rel.target, event["PersonA"])
                and (
                    rel_graph.get_connection(rel.target, event["PersonA"]).friendship
                    >= threshold
                )
                and not rel_graph.get_connection(rel.target, event["PersonA"]).has_tags(
                    RelationshipTag.Friend
                )
                and not rel.has_tags(RelationshipTag.Friend)
                and rel.friendship >= threshold
            ):
                eligible_characters.append(world.get_gameobject(rel.target))

        if eligible_characters:
            return engine.rng.choice(eligible_characters)
        return None

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)
        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.Friend
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.Friend
        )

    return LifeEventType(
        name="BecomeFriends",
        roles=[
            EventRoleType(name="PersonA", components=[GameCharacter]),
            EventRoleType(name="PersonB", binder_fn=bind_potential_friend),
        ],
        execute_fn=execute,
        probability=probability,
    )


def become_enemies_event(
    threshold: int = -25, probability: float = 1.0
) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def potential_enemy_filter(
        world: World, event: LifeEvent, gameobject: GameObject
    ) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)
        if rel_graph.has_connection(
            event["PersonA"], gameobject.id
        ) and rel_graph.has_connection(gameobject.id, event["PersonA"]):
            return (
                rel_graph.get_connection(event["PersonA"], gameobject.id).friendship
                <= threshold
                and rel_graph.get_connection(gameobject.id, event["PersonA"]).friendship
                <= threshold
                and not rel_graph.get_connection(
                    event["PersonA"], gameobject.id
                ).has_tags(RelationshipTag.Enemy)
            )
        else:
            return False

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)
        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.Enemy
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.Enemy
        )

    return LifeEventType(
        name="BecomeEnemies",
        roles=[
            EventRoleType(name="PersonA", components=[GameCharacter]),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=potential_enemy_filter,
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def start_dating_event(threshold: int = 25, probability: float = 0.5) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def potential_partner_filter(
        world: World, event: LifeEvent, gameobject: GameObject
    ) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)
        if rel_graph.has_connection(
            event["PersonA"], gameobject.id
        ) and rel_graph.has_connection(gameobject.id, event["PersonA"]):
            return (
                rel_graph.get_connection(event["PersonA"], gameobject.id).romance
                >= threshold
                and rel_graph.get_connection(gameobject.id, event["PersonA"]).romance
                >= threshold
            )
        else:
            return False

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.SignificantOther
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.SignificantOther
        )

        person_a = world.get_gameobject(event["PersonA"])
        person_b = world.get_gameobject(event["PersonB"])

        person_a.add_component(
            Dating(
                partner_id=person_b.id,
                partner_name=str(person_b.get_component(GameCharacter).name),
            )
        )
        person_b.add_component(
            Dating(
                partner_id=person_a.id,
                partner_name=str(person_a.get_component(GameCharacter).name),
            )
        )

    return LifeEventType(
        name="StartDating",
        roles=[
            EventRoleType(
                name="PersonA", components=[GameCharacter], filter_fn=is_single
            ),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=join_filters(potential_partner_filter, is_single),
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def dating_break_up_event(
    threshold: int = -15, probability: float = 0.5
) -> LifeEventType:
    """Defines an event where two characters stop dating"""

    def current_partner_filter(
        world: World, event: LifeEvent, gameobject: GameObject
    ) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)

        if gameobject.has_component(Dating):
            if gameobject.get_component(Dating).partner_id == event["PersonA"]:
                return (
                    rel_graph.get_connection(event["PersonA"], gameobject.id).romance
                    < threshold
                )

        return False

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).remove_tags(
            RelationshipTag.SignificantOther
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).remove_tags(
            RelationshipTag.SignificantOther
        )

        world.get_gameobject(event["PersonA"]).remove_component(Dating)
        world.get_gameobject(event["PersonB"]).remove_component(Dating)

    return LifeEventType(
        name="DatingBreakUp",
        roles=[
            EventRoleType(name="PersonA", components=[GameCharacter]),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=current_partner_filter,
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def divorce_event(threshold: int = -25, probability: float = 0.5) -> LifeEventType:
    """Defines an event where two characters stop dating"""

    def current_partner_filter(
        world: World, event: LifeEvent, gameobject: GameObject
    ) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)

        if gameobject.has_component(Married):
            if gameobject.get_component(Married).partner_id == event["PersonA"]:
                return (
                    rel_graph.get_connection(event["PersonA"], gameobject.id).romance
                    < threshold
                )

        return False

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).remove_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).remove_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )

        world.get_gameobject(event["PersonA"]).remove_component(Married)
        world.get_gameobject(event["PersonB"]).remove_component(Married)

    return LifeEventType(
        name="GotDivorced",
        roles=[
            EventRoleType(name="PersonA", components=[GameCharacter]),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=current_partner_filter,
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def marriage_event(threshold: int = 35, probability: float = 0.5) -> LifeEventType:
    """Defines an event where two characters become friends"""

    def potential_partner_filter(
        world: World, event: LifeEvent, gameobject: GameObject
    ) -> bool:
        rel_graph = world.get_resource(RelationshipGraph)
        if (
            gameobject.has_component(Dating)
            and gameobject.get_component(Dating).partner_id == event["PersonA"]
        ):
            if rel_graph.has_connection(
                event["PersonA"], gameobject.id
            ) and rel_graph.has_connection(gameobject.id, event["PersonA"]):
                return (
                    rel_graph.get_connection(event["PersonA"], gameobject.id).romance
                    >= threshold
                    and rel_graph.get_connection(
                        gameobject.id, event["PersonA"]
                    ).romance
                    >= threshold
                )

        return False

    def execute(world: World, event: LifeEvent) -> None:
        rel_graph = world.get_resource(RelationshipGraph)

        rel_graph.get_connection(event["PersonA"], event["PersonB"]).add_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )
        rel_graph.get_connection(event["PersonB"], event["PersonA"]).add_tags(
            RelationshipTag.SignificantOther | RelationshipTag.Spouse
        )

        person_a = world.get_gameobject(event["PersonA"])
        person_b = world.get_gameobject(event["PersonB"])

        person_a.remove_component(Dating)
        person_b.remove_component(Dating)

        person_a.add_component(
            Married(
                partner_id=person_b.id,
                partner_name=str(person_b.get_component(GameCharacter).name),
            )
        )
        person_b.add_component(
            Married(
                partner_id=person_a.id,
                partner_name=str(person_a.get_component(GameCharacter).name),
            )
        )

    return LifeEventType(
        name="GotMarried",
        roles=[
            EventRoleType(
                name="PersonA", components=[GameCharacter], filter_fn=is_single
            ),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=join_filters(potential_partner_filter, is_single),
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def depart_due_to_unemployment() -> LifeEventType:
    def bind_unemployed_character(world: World, event: LifeEvent):
        eligible_characters: List[GameObject] = []
        for _, unemployed in world.get_component(Unemployed):
            if unemployed.duration_days > 30:
                eligible_characters.append(unemployed.gameobject)
        if eligible_characters:
            return world.get_resource(NeighborlyEngine).rng.choice(eligible_characters)
        return None

    def effect(world: World, event: LifeEvent):
        world.delete_gameobject(event["Person"])

    return LifeEventType(
        name="DepartTown",
        roles=[EventRoleType(name="Person", binder_fn=bind_unemployed_character)],
        execute_fn=effect,
    )


def pregnancy_event(probability: float = 0.3) -> LifeEventType:
    """Defines an event where two characters stop dating"""

    def can_get_pregnant_filter(
        world: World, event: LifeEvent, gameobject: GameObject
    ) -> bool:
        return gameobject.get_component(
            GameCharacter
        ).can_get_pregnant and not gameobject.has_component(Pregnant)

    def current_partner_filter(
        world: World, event: LifeEvent, gameobject: GameObject
    ) -> bool:
        return (
            gameobject.has_component(Married)
            and gameobject.get_component(Married).partner_id == event["PersonA"]
        )

    def execute(world: World, event: LifeEvent) -> None:
        due_date = SimDateTime.from_iso_str(
            world.get_resource(SimDateTime).to_iso_str()
        )
        due_date.increment(months=9)

        world.get_gameobject(event["PersonA"]).add_component(
            Pregnant(
                partner_name=str(
                    world.get_gameobject(event["PersonB"])
                    .get_component(GameCharacter)
                    .name
                ),
                partner_id=event["PersonB"],
                due_date=due_date,
            )
        )

    return LifeEventType(
        name="GotDivorced",
        roles=[
            EventRoleType(
                name="PersonA",
                components=[GameCharacter],
                filter_fn=can_get_pregnant_filter,
            ),
            EventRoleType(
                name="PersonB",
                components=[GameCharacter],
                filter_fn=current_partner_filter,
            ),
        ],
        execute_fn=execute,
        probability=probability,
    )


def retire_event(probability: float = 0.4) -> LifeEventType:
    """
    Event for characters retiring from working after reaching elder status

    Parameters
    ----------
    probability: float
        Probability that a character will retire from their job
        when they are an elder

    Returns
    -------
    LifeEventType
        LifeEventType instance with all configuration defined
    """

    def bind_retiree(world: World, event: LifeEvent):
        eligible_characters: List[GameObject] = []
        for gid, _ in world.get_components(Elder, Occupation):
            gameobject = world.get_gameobject(gid)
            if not gameobject.has_component(Retired):
                eligible_characters.append(gameobject)
        if eligible_characters:
            return world.get_resource(NeighborlyEngine).rng.choice(eligible_characters)
        return None

    def execute(world: World, event: LifeEvent):
        retiree = world.get_gameobject(event["Retiree"])
        retiree.remove_component(Occupation)
        retiree.add_component(Retired())

    return LifeEventType(
        name="Retire",
        roles=[EventRoleType(name="Retiree", binder_fn=bind_retiree)],
        execute_fn=execute,
        probability=probability,
    )
