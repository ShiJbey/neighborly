"""Other event implementations.

"""

from __future__ import annotations

import random
from typing import Any, Optional

from neighborly.components.business import Business, JobRole, Occupation
from neighborly.components.character import Character, LifeStage, Sex
from neighborly.components.relationship import Relationship, Relationships
from neighborly.components.residence import Resident, ResidentialUnit, Vacant
from neighborly.components.settlement import District
from neighborly.datetime import SimDate
from neighborly.ecs import Active, GameObject
from neighborly.events.defaults import (
    BusinessClosedEvent,
    ChangeResidenceEvent,
    DepartSettlement,
    LeaveJob,
)
from neighborly.helpers.location import add_frequented_location
from neighborly.helpers.relationship import (
    get_relationship,
    get_relationships_with_traits,
)
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, has_trait, remove_trait
from neighborly.life_event import LifeEvent
from neighborly.simulation import Simulation


class StartANewJob(LifeEvent):
    """A character will attempt to find a job."""

    base_probability = 0.7

    subject: GameObject
    """The character started the new job."""
    business: GameObject
    """The business they started working at."""
    role: GameObject
    """The role they work."""

    @staticmethod
    def number_children_consideration(event: StartANewJob) -> float:
        """Consider the number of children the character has."""
        subject = event.roles["subject"]
        child_count = len(get_relationships_with_traits(subject, "child"))

        if child_count != 0:
            return min(1.0, child_count / 5.0)

        return -1

    @staticmethod
    def boldness_consideration(event: StartANewJob) -> float:
        """Considers the subject's boldness stat."""
        return get_stat(event.roles["subject"], "boldness").normalized

    @staticmethod
    def reliability_consideration(event: StartANewJob) -> float:
        """Considers the subjects reliability stat."""
        return get_stat(event.roles["subject"], "reliability").normalized

    @staticmethod
    def time_unemployed_consideration(event: StartANewJob) -> float:
        """Calculate consideration score based on the amount of time unemployed."""
        subject = event.roles["subject"]

        if unemployed := subject.try_component(Unemployed):
            current_date = subject.world.resources.get_resource(SimDate)
            months_unemployed = (
                current_date.total_months - unemployed.timestamp.total_months
            )
            return min(1.0, float(months_unemployed) / 6.0)

        return -1

    @staticmethod
    def relationship_with_owner(event: StartANewJob) -> float:
        """Considers the subject's reputation with the business' owner."""
        subject = event.roles["subject"]
        business_owner = event.roles["business"].get_component(Business).owner

        if business_owner is not None:
            return get_stat(
                get_relationship(business_owner, subject),
                "reputation",
            ).normalized

        return -1

    @staticmethod
    def life_stage_consideration(event: GetMarried) -> float:
        """Check the life stage of both partners"""
        subject = event.roles["subject"]

        life_stage = subject.get_component(Character).life_stage

        if life_stage in (LifeStage.CHILD, life_stage.ADOLESCENT):
            return 0.0

        if life_stage in (life_stage.YOUNG_ADULT, life_stage.ADULT):
            return 0.9

        return 0.1

    @staticmethod
    def retired_consideration(event: GetMarried) -> float:
        """Check the life stage of both partners"""
        subject = event.roles["subject"]

        if has_trait(self.subject, "retired"):
            return 0.2

        return -1

    @property
    def description(self) -> str:
        return (
            f"{self.subject.name} started a new job as a "
            f"{self.role.name} at {self.business.name}."
        )


class StartBusiness(LifeEvent):
    """Character starts a specific business."""

    def __init__(
        self,
        subject: GameObject,
        business: GameObject,
        district: GameObject,
        settlement: GameObject,
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, True),
                EventRole("business", business, True),
                EventRole("district", district),
                EventRole("settlement", settlement),
            ],
        )

    @staticmethod
    def has_job_consideration(event: StartBusiness) -> float:
        """check if the character already has a job."""
        if event.roles["subject"].has_component(Occupation):
            return 0

        return -1

    @staticmethod
    def boldness_consideration(event: StartBusiness) -> float:
        """Considers the subject's boldness stat."""
        return get_stat(event.roles["subject"], "boldness").normalized

    @staticmethod
    def reliability_consideration(event: StartBusiness) -> float:
        """Considers the subjects reliability stat."""
        return get_stat(event.roles["subject"], "reliability").normalized

    @staticmethod
    def time_unemployed_consideration(event: StartBusiness) -> float:
        """Calculate consideration score based on the amount of time unemployed."""
        subject = event.roles["subject"]

        if unemployed := subject.try_component(Unemployed):
            current_date = subject.world.resources.get_resource(SimDate)
            months_unemployed = (
                current_date.total_months - unemployed.timestamp.total_months
            )
            return min(1.0, float(months_unemployed) / 6.0)

        return -1

    def __str__(self) -> str:
        subject = self.roles["subject"]
        business = self.roles["business"]
        district = self.roles["district"]
        settlement = self.roles["settlement"]

        return (
            f"{subject.name} opened a new business, "
            f"{business.name}, in the {district.name} district of "
            f"{settlement.name}."
        )


class StartDating(LifeEvent):
    """Event dispatched when two characters start dating."""

    base_probability = 0.5

    def __init__(self, subject: GameObject, partner: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, True),
                EventRole("partner", partner, True),
            ],
        )

    def execute(self) -> None:
        subject_0 = self.roles["subject"]
        partner = self.roles["partner"]

        add_trait(get_relationship(subject_0, partner), "dating")
        add_trait(get_relationship(partner, subject_0), "dating")

    @staticmethod
    def subject_has_crush(event: StartDating) -> float:
        """Consider if the subject has a crush on the other person."""
        subject = event.roles["subject"]
        other = event.roles["partner"]

        if has_trait(get_relationship(subject, other), "crush"):
            return 0.7

        return 0.2

    @staticmethod
    def other_has_crush(event: StartDating) -> float:
        """Consider if the other person has a crush on the subject."""
        subject = event.roles["subject"]
        other = event.roles["partner"]

        if has_trait(get_relationship(other, subject), "crush"):
            return 0.7

        return 0.2

    @staticmethod
    def romance_to_partner(event: StartDating) -> float:
        """Consider the romance from the partner to the subject."""
        return (
            get_stat(
                get_relationship(event.roles["subject"], event.roles["partner"]),
                "romance",
            ).normalized
            ** 2
        )

    @staticmethod
    def romance_to_subject(event: StartDating) -> float:
        """Consider the romance from the partner to the subject."""
        return (
            get_stat(
                get_relationship(event.roles["partner"], event.roles["subject"]),
                "romance",
            ).normalized
            ** 2
        )

    @staticmethod
    def partner_already_dating(event: StartDating) -> float:
        """Consider if the partner is already dating someone."""
        if len(get_relationships_with_traits(event.roles["partner"], "dating")) > 0:
            return 0.05

        if len(get_relationships_with_traits(event.roles["partner"], "spouse")) > 0:
            return 0.05

        return -1

    def __str__(self) -> str:
        subject_0 = self.roles["subject"]
        partner = self.roles["partner"]
        return f"{subject_0.name} and {partner.name} started dating."


class GetMarried(LifeEvent):
    """Event dispatched when two characters get married."""

    def __init__(self, subject: GameObject, partner: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, True),
                EventRole("subject", partner, True),
            ],
        )

    @staticmethod
    def life_stage_consideration(event: GetMarried) -> float:
        """Check the life stage of both partners"""
        subject_0, subject_1 = event.roles.get_all("subject")

        subject_0_life_stage = subject_0.get_component(Character).life_stage
        subject_1_life_stage = subject_1.get_component(Character).life_stage

        if (
            subject_0_life_stage < LifeStage.YOUNG_ADULT
            or subject_1_life_stage < LifeStage.YOUNG_ADULT
        ):
            return 0.0

        if (
            subject_0_life_stage > LifeStage.ADULT
            or subject_1_life_stage > LifeStage.ADULT
        ):
            return 0.05

        return -1

    @staticmethod
    def romance_to_partner(event: StartDating) -> float:
        """Consider the romance from the partner to the subject."""
        subject_0, subject_1 = event.roles.get_all("subject")

        return get_stat(get_relationship(subject_0, subject_1), "romance").normalized

    @staticmethod
    def romance_to_subject(event: StartDating) -> float:
        """Consider the romance from the partner to the subject."""
        subject_0, subject_1 = event.roles.get_all("subject")

        return get_stat(get_relationship(subject_1, subject_0), "romance").normalized

    def __str__(self) -> str:
        subject_0, subject_1 = self.roles.get_all("subject")

        return f"{subject_0.name} and {subject_1.name} got married."


class GetDivorced(LifeEvent):
    """Dispatched to officially divorce two married characters."""

    def __init__(self, subject: GameObject, ex_spouse: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, True),
                EventRole("ex_spouse", ex_spouse, True),
            ],
        )

    @staticmethod
    def romance_to_spouse(event: GetDivorced) -> float:
        """Consider how in-love the subject is with the ex_spouse"""
        return (
            1.0
            - get_stat(
                get_relationship(event.roles["subject"], event.roles["ex_spouse"]),
                "romance",
            ).normalized
        )

    def execute(self) -> None:
        initiator = self.roles["subject"]
        ex_spouse = self.roles["ex_spouse"]

        remove_trait(get_relationship(initiator, ex_spouse), "spouse")
        remove_trait(get_relationship(ex_spouse, initiator), "spouse")

        add_trait(get_relationship(initiator, ex_spouse), "ex_spouse")
        add_trait(get_relationship(ex_spouse, initiator), "ex_spouse")

        get_stat(get_relationship(ex_spouse, initiator), "romance").base_value -= 25

        # initiator finds new place to live or departs
        vacant_housing = initiator.world.get_components((ResidentialUnit, Vacant))

        if vacant_housing:
            _, (residence, _) = vacant_housing[0]
            ChangeResidenceEvent(
                initiator, new_residence=residence.gameobject, is_owner=True
            ).dispatch()

        else:
            ChangeResidenceEvent(initiator, new_residence=None).dispatch()
            DepartSettlement(initiator).dispatch()

    def __str__(self) -> str:
        initiator = self.roles["subject"]
        ex_spouse = self.roles["ex_spouse"]

        return f"{initiator.name} divorced from {ex_spouse.name}."


class BreakUp(LifeEvent):
    """Dispatched to officially break up a dating relationship between characters."""

    def __init__(self, subject: GameObject, ex_partner: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, True),
                EventRole("ex_partner", ex_partner, True),
            ],
        )

    @staticmethod
    def romance_to_partner(event: StartDating) -> float:
        """Consider the romance from the partner to the subject."""
        return (
            1.0
            - get_stat(
                get_relationship(event.roles["subject"], event.roles["ex_partner"]),
                "romance",
            ).normalized
        )

    def execute(self) -> None:
        initiator = self.roles["subject"]
        ex_partner = self.roles["ex_partner"]

        remove_trait(get_relationship(initiator, ex_partner), "dating")
        remove_trait(get_relationship(ex_partner, initiator), "dating")

        add_trait(get_relationship(initiator, ex_partner), "ex_partner")
        add_trait(get_relationship(ex_partner, initiator), "ex_partner")

        get_stat(get_relationship(ex_partner, initiator), "romance").base_value -= 15

    def __str__(self) -> str:
        initiator = self.roles["subject"]
        ex_partner = self.roles["ex_partner"]

        return f"{initiator.name} broke up with " f"{ex_partner.name}."


class GetPregnant(LifeEvent):
    """Characters have a chance of getting pregnant while in romantic relationships."""

    base_probability = 0.5

    def __init__(
        self,
        subject: GameObject,
        partner: GameObject,
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=[EventRole("subject", subject, True), EventRole("partner", partner)],
        )

    @staticmethod
    def check_if_pregnant(event: GetPregnant) -> float:
        """Check if the subject is already pregnant"""
        if event.roles["subject"].has_component(Pregnant):
            return 0.0
        return -1.0

    @staticmethod
    def proper_sex_consideration(event: GetPregnant) -> float:
        """Check that characters are the right sex to procreate."""
        subject = event.roles["subject"]
        partner = event.roles["partner"]

        if subject.get_component(Character).sex == Sex.MALE:
            return 0.0

        if partner.get_component(Character).sex == Sex.FEMALE:
            return 0.0

        return -1

    @staticmethod
    def fertility_consideration(event: GetPregnant) -> float:
        """Check the fertility of the subject."""
        return get_stat(event.roles["subject"], "fertility").value

    @staticmethod
    def partner_fertility_consideration(event: GetPregnant) -> float:
        """Check fertility of the partner."""
        return get_stat(event.roles["partner"], "fertility").value

    def execute(self) -> None:
        subject = self.roles["subject"]
        partner = self.roles["partner"]

        due_date = self.world.resources.get_resource(SimDate).copy()
        due_date.increment(months=9)

        subject.add_component(Pregnant(partner=partner, due_date=due_date))

    def __str__(self) -> str:
        subject = self.roles["subject"]
        partner = self.roles["partner"]

        return f"{subject.name} got pregnant by {partner.name}."


class Retire(LifeEvent):
    """Simulates a character retiring from their position at a business.

    When a business owner retires they may appoint a current employee or family member
    to become the owner of the business. If they can't find a suitable successor,
    then they shut the business down and everyone is laid-off.

    If the retiree is an employee, they are just removed from their role and business
    continues as usual.
    """

    base_probability = 0.4

    def __init__(
        self,
        subject: GameObject,
        business: GameObject,
        job_role: GameObject,
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, log_event=True),
                EventRole("business", business, log_event=True),
                EventRole("job_role", job_role),
            ],
        )

    @staticmethod
    def life_stage_consideration(event: Retire) -> float:
        """Calculate probability of retiring based on life stage."""
        subject = event.roles["subject"]
        life_stage = subject.get_component(Character).life_stage

        if life_stage < LifeStage.SENIOR:
            return 0.01

        return 0.8

    def __str__(self) -> str:
        character = self.roles["subject"]
        occupation = self.roles["job_role"]
        business = self.roles["business"]

        return (
            f"{character.name} retired from their "
            f"position as {occupation.name} at {business.name}."
        )


class DepartDueToUnemployment(LifeEvent):
    """Character leave the settlement and the simulation."""

    base_probability = 0.3

    def __init__(self, subject: GameObject, reason: str = "") -> None:
        super().__init__(
            world=subject.world, roles=[EventRole("subject", subject)], reason=reason
        )

    @staticmethod
    def employment_spouse_consideration(event: DepartDueToUnemployment) -> float:
        """Calculate consideration score for if the character is married."""
        subject = event.roles["subject"]
        if len(get_relationships_with_traits(subject, "spouse")) > 0:
            return 0.7
        return -1

    @staticmethod
    def employment_children_consideration(event: DepartDueToUnemployment) -> float:
        """Calculate a consideration score based on a character's number of children/"""
        subject = event.roles["subject"]

        child_count = len(get_relationships_with_traits(subject, "child"))

        if child_count != 0:
            return min(1.0, child_count / 5.0)

        return -1

    @staticmethod
    def has_occupation_consideration(event: DepartDueToUnemployment) -> float:
        """Calculate consideration score for if the character already has a job"""
        subject = event.roles["subject"]
        if subject.has_component(Occupation):
            return 0.0

        return -1

    @staticmethod
    def reliability_consideration(event: DepartDueToUnemployment) -> float:
        """Calculate consideration score for a character's reliability"""
        return get_stat(event.roles["subject"], "reliability").normalized

    @staticmethod
    def time_unemployed_consideration(event: DepartDueToUnemployment) -> float:
        """Calculate consideration score based on the amount of time unemployed."""
        subject = event.roles["subject"]
        if unemployed := subject.try_component(Unemployed):
            current_date = subject.world.resources.get_resource(SimDate)
            months_unemployed = (
                current_date.total_months - unemployed.timestamp.total_months
            )
            return min(1.0, float(months_unemployed) / 6.0)
        return -1

    @staticmethod
    def spouse_employment_consideration(event: DepartDueToUnemployment) -> float:
        """Veto if spouse has a job"""
        subject = event.roles["subject"]

        spousal_relationships = get_relationships_with_traits(subject, "spouse")

        # Depart if none of their spouses has a job either
        if any(
            rel.get_component(Relationship).target.has_component(Occupation)
            for rel in spousal_relationships
        ):
            return 0

        return -1

    def execute(self) -> None:
        character = self.roles["subject"]
        DepartSettlement(subject=character, reason="unemployment").dispatch()

    def __str__(self):
        subject = self.roles["subject"]
        return (
            f"{subject.name} decided to depart from the settlement due to unemployment."
        )


class BecomeFriends(LifeEvent):
    """Two characters become friends."""

    base_probability = 0.0

    def __init__(self, subject: GameObject, other: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=(
                EventRole("subject", subject, True),
                EventRole("other", other, True),
            ),
        )

    @staticmethod
    def other_friend_count_consideration(event: BecomeFriends) -> float:
        """Consider the number of friends the other character already has."""
        return (
            1.0
            - min(
                len(get_relationships_with_traits(event.roles["other"], "friend"))
                / 8.0,
                1.0,
            )
        ) ** 2

    @staticmethod
    def friend_count_consideration(event: BecomeFriends) -> float:
        """Consider the number of friends the subject already has."""
        return (
            1.0
            - min(
                len(get_relationships_with_traits(event.roles["subject"], "friend"))
                / 8.0,
                1.0,
            )
        ) ** 2

    @staticmethod
    def other_reputation_consideration(event: BecomeFriends) -> float:
        """Consider the reputation from the subject to the other person."""
        return (
            get_stat(
                get_relationship(event.roles["other"], event.roles["subject"]),
                "reputation",
            ).normalized
            ** 2
        )

    @staticmethod
    def subject_reputation_consideration(event: BecomeFriends) -> float:
        """Consider the reputation from the subject to the other person."""
        return (
            get_stat(
                get_relationship(event.roles["subject"], event.roles["other"]),
                "reputation",
            ).normalized
            ** 2
        )

    @staticmethod
    def are_enemies(event: BecomeFriends) -> float:
        """Consider if they are enemies."""
        if has_trait(
            get_relationship(event.roles["other"], event.roles["subject"]), "enemy"
        ):
            return 0.01
        return -1

    def __str__(self) -> str:
        subject = self.roles["subject"]
        other = self.roles["other"]
        return f"{subject.name} and {other.name} became friends."


class DissolveFriendship(LifeEvent):
    """Two characters stop being friends."""

    base_probability = 0.0

    def __init__(self, subject: GameObject, other: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=(
                EventRole("subject", subject, True),
                EventRole("other", other, True),
            ),
        )

    @staticmethod
    def other_reputation_consideration(event: BecomeFriends) -> float:
        """Consider the reputation from the subject to the other person."""
        return (
            1
            - get_stat(
                get_relationship(event.roles["other"], event.roles["subject"]),
                "reputation",
            ).normalized
            ** 2
        )

    @staticmethod
    def subject_reputation_consideration(event: BecomeFriends) -> float:
        """Consider the reputation from the subject to the other person."""
        return (
            1
            - get_stat(
                get_relationship(event.roles["subject"], event.roles["other"]),
                "reputation",
            ).normalized
            ** 2
        )

    def execute(self) -> None:
        subject = self.roles["subject"]
        other = self.roles["other"]
        remove_trait(get_relationship(subject, other), "friend")
        remove_trait(get_relationship(other, subject), "friend")

    def __str__(self) -> str:
        subject = self.roles["subject"]
        other = self.roles["other"]
        return f"{subject.name} and {other.name} stopped being friends."


class BecomeEnemies(LifeEvent):
    """Two characters become enemies."""

    base_probability = 0.5

    def __init__(self, subject: GameObject, other: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=(
                EventRole("subject", subject, True),
                EventRole("other", other, True),
            ),
        )

    @staticmethod
    def are_friends(event: BecomeEnemies) -> float:
        """Consider if they are friends."""
        if has_trait(
            get_relationship(event.roles["other"], event.roles["subject"]), "friend"
        ):
            return 0.01
        return -1

    @staticmethod
    def other_reputation_consideration(event: BecomeEnemies) -> float:
        """Consider the reputation from the subject to the other person."""
        return (
            1
            - get_stat(
                get_relationship(event.roles["other"], event.roles["subject"]),
                "reputation",
            ).normalized
        ) ** 2

    @staticmethod
    def subject_reputation_consideration(event: BecomeEnemies) -> float:
        """Consider the reputation from the subject to the other person."""
        return (
            1
            - get_stat(
                get_relationship(event.roles["subject"], event.roles["other"]),
                "reputation",
            ).normalized
        ) ** 2

    def execute(self) -> None:
        subject = self.roles["subject"]
        other = self.roles["other"]
        add_trait(get_relationship(subject, other), "enemy")
        add_trait(get_relationship(other, subject), "enemy")

    def __str__(self) -> str:
        subject = self.roles["subject"]
        other = self.roles["other"]
        return f"{subject.name} and {other.name} became enemies."


class DissolveEnmity(LifeEvent):
    """Two characters stop being enemies."""

    base_probability = 0.2

    def __init__(self, subject: GameObject, other: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=(
                EventRole("subject", subject, True),
                EventRole("other", other, True),
            ),
        )

    @staticmethod
    def other_reputation_consideration(event: BecomeFriends) -> float:
        """Consider the reputation from the subject to the other person."""
        return (
            get_stat(
                get_relationship(event.roles["other"], event.roles["subject"]),
                "reputation",
            ).normalized
            ** 2
        )

    @staticmethod
    def subject_reputation_consideration(event: BecomeFriends) -> float:
        """Consider the reputation from the subject to the other person."""
        return (
            get_stat(
                get_relationship(event.roles["subject"], event.roles["other"]),
                "reputation",
            ).normalized
            ** 2
        )

    def execute(self) -> None:
        subject = self.roles["subject"]
        other = self.roles["other"]
        remove_trait(get_relationship(subject, other), "enemy")
        remove_trait(get_relationship(other, subject), "enemy")

    def __str__(self) -> str:
        subject = self.roles["subject"]
        other = self.roles["other"]
        return f"{subject.name} and {other.name} stopped being enemies."


class FormCrush(LifeEvent):
    """A character forms a new crush on someone."""

    base_probability = 0.2

    def __init__(self, subject: GameObject, other: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=(
                EventRole("subject", subject, True),
                EventRole("other", other, False),
            ),
        )

    @staticmethod
    def current_crush_consideration(event: FormCrush) -> float:
        """Consider a character's current crush."""
        subject = event.roles["subject"]
        crush_relationships = get_relationships_with_traits(subject, "crush")

        if crush_relationships:
            relationship = crush_relationships[0]
            if relationship.is_active:
                return 1 - get_stat(relationship, "romance").normalized

        return -1

    @staticmethod
    def romance_consideration(event: FormCrush) -> float:
        """Consider a character's romance value."""
        return (
            get_stat(
                get_relationship(event.roles["subject"], event.roles["other"]),
                "romance",
            ).normalized
            ** 2
        )

    def __str__(self) -> str:
        subject = self.roles["subject"]
        other = self.roles["other"]
        return f"{subject.name} formed a crush on {other.name}"


class TryFindOwnPlace(LifeEvent):
    """Adults living with parents will try to find their own residence."""

    base_probability = 0.4

    def __init__(self, subject: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=(EventRole("subject", subject, True),),
        )

    @staticmethod
    def boldness_consideration(event: StartANewJob) -> float:
        """Considers the subject's boldness stat."""
        return get_stat(event.roles["subject"], "boldness").normalized

    @staticmethod
    def reliability_consideration(event: StartANewJob) -> float:
        """Considers the subjects reliability stat."""
        return get_stat(event.roles["subject"], "reliability").normalized

    def __str__(self) -> str:
        subject = self.roles["subject"]
        return f"{subject.name} moved out of their parent's home."


class PromotedToBusinessOwner(LifeEvent):
    """Simulate a character being promoted to the owner of a business."""

    base_probability = 0.4

    def __init__(
        self,
        subject: GameObject,
        business: GameObject,
        former_owner: GameObject,
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=(
                EventRole("subject", subject, True),
                EventRole("business", business, True),
                EventRole("former_owner", former_owner),
            ),
        )

    @staticmethod
    def relationship_with_owner(event: LifeEvent) -> float:
        """Considers the subject's reputation with the business' owner."""
        subject = event.roles["subject"]
        business_owner = event.roles["business"].get_component(Business).owner

        if business_owner is not None:
            return (
                get_stat(
                    get_relationship(business_owner, subject),
                    "reputation",
                ).normalized
                ** 2
            )

        return -1

    @staticmethod
    def boldness_consideration(event: LifeEvent) -> float:
        """Considers the subject's boldness stat."""
        return get_stat(event.roles["subject"], "boldness").normalized ** 3

    @staticmethod
    def reliability_consideration(event: LifeEvent) -> float:
        """Considers the subjects reliability stat."""
        return get_stat(event.roles["subject"], "reliability").normalized ** 2

    def __str__(self) -> str:
        subject = self.roles["subject"]
        business = self.roles["business"]
        former_owner = self.roles["former_owner"]

        return (
            f"{subject.name} was succeeded {former_owner.name} as the owner "
            f"of {business.name}"
        )


class JobPromotion(LifeEvent):
    """The character is promoted at their job from a lower role to a higher role."""

    base_probability = 0.4

    def __init__(
        self,
        subject: GameObject,
        business: GameObject,
        old_role: GameObject,
        new_role: GameObject,
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=(
                EventRole("subject", subject, True),
                EventRole("business", business, True),
                EventRole("old_role", old_role),
                EventRole("new_role", new_role),
            ),
        )

    @staticmethod
    def relationship_with_owner(event: LifeEvent) -> float:
        """Considers the subject's reputation with the business' owner."""
        subject = event.roles["subject"]
        business_owner = event.roles["business"].get_component(Business).owner

        if business_owner is not None:
            return get_stat(
                get_relationship(business_owner, subject),
                "reputation",
            ).normalized

        return -1

    @staticmethod
    def boldness_consideration(event: LifeEvent) -> float:
        """Considers the subject's boldness stat."""
        return get_stat(event.roles["subject"], "boldness").normalized

    @staticmethod
    def reliability_consideration(event: LifeEvent) -> float:
        """Considers the subjects reliability stat."""
        return get_stat(event.roles["subject"], "reliability").normalized

    def __str__(self) -> str:
        subject = self.roles["subject"]
        business = self.roles["business"]
        old_role = self.roles["old_role"]
        new_role = self.roles["new_role"]

        return (
            f"{subject.name} was promoted from {old_role.name} to "
            f"{new_role.name} at {business.name}."
        )


class FiredFromJob(LifeEvent):
    """The character is fired from their job."""

    base_probability = 0.1

    def __init__(
        self, subject: GameObject, business: GameObject, job_role: GameObject
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=(
                EventRole("subject", subject, True),
                EventRole("business", business),
                EventRole("job_role", job_role),
            ),
        )

    @staticmethod
    def stewardship_consideration(event: LifeEvent) -> float:
        """Considers the subjects reliability stat."""
        return 1 - get_stat(event.roles["subject"], "stewardship").normalized

    @staticmethod
    def reliability_consideration(event: LifeEvent) -> float:
        """Considers the subjects reliability stat."""
        return 1 - get_stat(event.roles["subject"], "reliability").normalized ** 2

    def __str__(self) -> str:
        subject = self.roles["subject"]
        business = self.roles["business"]
        job_role = self.roles["job_role"]

        return (
            f"{subject.name} was fired from their role as a "
            f"{job_role.name} at {business.name}."
        )


def load_plugin(sim: Simulation) -> None:
    """Load plugin content."""

    register_life_event_type(sim, StartANewJob)
    register_life_event_type(sim, StartBusiness)
    register_life_event_type(sim, StartDating)
    register_life_event_type(sim, GetMarried)
    register_life_event_type(sim, GetDivorced)
    register_life_event_type(sim, BreakUp)
    register_life_event_type(sim, GetPregnant)
    register_life_event_type(sim, Retire)
    register_life_event_type(sim, DepartDueToUnemployment)
    register_life_event_type(sim, BecomeFriends)
    register_life_event_type(sim, DissolveFriendship)
    register_life_event_type(sim, BecomeEnemies)
    register_life_event_type(sim, DissolveEnmity)
    register_life_event_type(sim, FormCrush)
    register_life_event_type(sim, TryFindOwnPlace)
    register_life_event_type(sim, FiredFromJob)
    register_life_event_type(sim, JobPromotion)
