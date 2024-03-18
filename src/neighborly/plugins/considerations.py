"""Default considerations."""

from neighborly.actions.base_types import ActionInstance
from neighborly.components.business import Business
from neighborly.datetime import SimDate
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import get_trait, has_trait


def stewardship_consideration(action: ActionInstance) -> float:
    """Considers the subjects reliability stat."""
    return 1 - get_stat(action.roles["subject"], "stewardship").normalized


def reliability_consideration(action: ActionInstance) -> float:
    """Considers the subjects reliability stat."""
    return 1 - get_stat(action.roles["subject"], "reliability").normalized ** 2


def boldness_consideration(action: ActionInstance) -> float:
    """Considers the subject's boldness stat."""
    return get_stat(action.roles["subject"], "boldness").normalized


def relationship_with_business_owner(action: ActionInstance) -> float:
    """Considers the subject's reputation with the business' owner."""
    subject = action.roles["subject"]
    business_owner = action.roles["business"].get_component(Business).owner

    if business_owner is not None:
        return get_stat(
            get_relationship(business_owner, subject),
            "reputation",
        ).normalized

    return -1


def are_friends(action: ActionInstance) -> float:
    """Consider if they are friends."""
    if has_trait(
        get_relationship(action.roles["other"], action.roles["subject"]), "friend"
    ):
        return 0.01
    return -1


def other_reputation_consideration(action: ActionInstance) -> float:
    """Consider the reputation from the subject to the other person."""
    return (
        1
        - get_stat(
            get_relationship(action.roles["other"], action.roles["subject"]),
            "reputation",
        ).normalized
    ) ** 2


def subject_reputation_consideration(action: ActionInstance) -> float:
    """Consider the reputation from the subject to the other person."""
    return (
        1
        - get_stat(
            get_relationship(action.roles["subject"], action.roles["other"]),
            "reputation",
        ).normalized
    ) ** 2


@staticmethod
    def has_job_consideration(event: StartBusiness) -> float:
        """check if the character already has a job."""
        if event.roles["subject"].has_component(Occupation):
            return 0

        return -1


def time_unemployed_consideration(action: ActionInstance) -> float:
    """Calculate consideration score based on the amount of time unemployed."""
    subject = action.roles["subject"]

    if not has_trait(subject, "unemployed"):
        return -1

    unemployed_trait = get_trait(subject, "unemployed")
    current_date = action.world.resources.get_resource(SimDate)

    months_unemployed = (
        current_date.total_months - unemployed_trait.data["timestamp"].total_months
    )

    return min(1.0, float(months_unemployed) / 6.0)

@staticmethod
    def number_children_consideration(event: StartANewJob) -> float:
        """Consider the number of children the character has."""
        subject = event.roles["subject"]
        child_count = len(get_relationships_with_traits(subject, "child"))

        if child_count != 0:
            return min(1.0, child_count / 5.0)

        return -1

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
