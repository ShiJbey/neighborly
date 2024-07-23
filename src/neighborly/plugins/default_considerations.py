"""A default set of Neighborly action considerations.

"""

from typing import Type, cast

from neighborly.action import Action, ActionConsideration, invert_cons
from neighborly.components.business import Business, Occupation
from neighborly.components.character import Character, LifeStage
from neighborly.components.relationship import IsSingle, Reputation, Romance
from neighborly.components.stats import (
    Boldness,
    Fertility,
    Honor,
    Luck,
    RomancePropensity,
    Sociability,
    StatComponent,
    WantForChildren,
    WantForMarriage,
    WantToWork,
)
from neighborly.ecs import GameObject
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.traits import get_time_with_trait
from neighborly.libraries import ActionConsiderationLibrary
from neighborly.plugins.actions import (
    AskOut,
    BecomeBusinessOwner,
    BreakUp,
    Divorce,
    FireEmployee,
    FormCrush,
    GetMarried,
    GetPregnant,
    ProposeMarriage,
    Retire,
    StartDating,
    TryFormCrush,
    TryGetJob,
)
from neighborly.simulation import Simulation


def existing_relationship_cons(action: Action) -> float:
    """Characters in relationships don't start dating or marriages with others."""

    performer = cast(GameObject, action.data["performer"])
    target = cast(GameObject, action.data["target"])

    if not performer.has_component(IsSingle):
        return 0.0

    if not target.has_component(IsSingle):
        return 0.0

    return -1


def has_occupation_consideration(action: Action) -> float:
    """Characters with occupations are not eligible to become business owners."""

    if isinstance(action, BecomeBusinessOwner):
        if action.character.has_component(Occupation):
            return 0

    return -1


def life_stage_consideration(action: Action) -> float:
    """Characters with occupations are not eligible to become business owners."""

    if isinstance(action, BecomeBusinessOwner):
        life_stage = action.character.get_component(Character).life_stage

        if life_stage < LifeStage.ADULT:
            return 0

        if life_stage < LifeStage.SENIOR:
            return 0.5

        # Seniors
        return 0.3

    return -1


def retirement_life_stage_cons(action: Action) -> float:
    """Senior characters are the only ones eligible to retire."""
    if isinstance(action, Retire):
        life_stage = action.character.get_component(Character).life_stage

        if life_stage == LifeStage.ADULT:
            return 0.05

        if life_stage == LifeStage.SENIOR:
            return 0.8

        # Everyone who is a young-adult or younger
        return 0.0

    return -1


def firing_owner_relationship_cons(action: Action) -> float:
    """Consider relationship of the owner to the potentially fired character."""
    if isinstance(action, FireEmployee):
        employee = action.character
        owner = action.business.get_component(Business).owner

        if owner is None:
            return -1

        relationship = get_relationship(owner, employee)

        normalized_reputation = relationship.get_component(Reputation).stat.normalized

        return 1 - (normalized_reputation**2)

    return -1


def marriage_time_dating_consideration(action: Action) -> float:
    """Consider how long you have been dating before getting married."""

    if isinstance(action, GetMarried):
        relationship = get_relationship(action.character, action.partner)
        months_dating = get_time_with_trait(relationship, "dating")
        years_dating = float(months_dating) / 12.0

        if months_dating == 0:
            return 0

        if years_dating > 3:
            return 0.9
        elif years_dating > 2:
            return 0.7
        elif years_dating > 1:
            return 0.5
        else:
            return 0.05

    return -1


def divorce_time_married_consideration(action: Action) -> float:
    """Consider how long you have been married before divorce."""

    if isinstance(action, Divorce):
        relationship = get_relationship(
            action.character.gameobject, action.partner.gameobject
        )
        months_married = get_time_with_trait(relationship, "spouse")
        years_married = float(months_married) / 12.0

        if months_married == 0:
            return 0

        if years_married > 30:
            return 0.1
        elif years_married > 20:
            return 0.2
        elif years_married > 10:
            return 0.4
        else:
            return 0.3

    return -1


def normalized_relationship_stat_consideration(
    owner: str, target: str, stat_type: Type[StatComponent]
) -> ActionConsideration:
    """Return the normalized value of the stat between the owner and target"""

    def wrapped_fn(action: Action) -> float:
        owner_obj = cast(GameObject, action.data[owner])
        target_obj = cast(GameObject, action.data[target])
        relationship = get_relationship(owner_obj, target_obj)

        return relationship.get_component(stat_type).stat.normalized

    return wrapped_fn


def normalized_stat_consideration(
    agent: str, stat_type: Type[StatComponent]
) -> ActionConsideration:
    """Return the normalized value of the stat as a consideration score."""

    def wrapped_fn(action: Action) -> float:

        return (
            cast(GameObject, action.data[agent])
            .get_component(stat_type)
            .stat.normalized
        )

    return wrapped_fn


def load_plugin(sim: Simulation) -> None:
    """Load plugin content into a simulation."""

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        TryGetJob.action_id(), normalized_stat_consideration("performer", WantToWork)
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        TryGetJob.action_id(), normalized_stat_consideration("performer", Honor)
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("become-business-owner", has_occupation_consideration)
    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("become-business-owner", life_stage_consideration)

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        AskOut.action_id(),
        normalized_relationship_stat_consideration("performer", "target", Romance),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        AskOut.action_id(),
        normalized_stat_consideration("performer", Boldness),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        AskOut.action_id(),
        normalized_stat_consideration("performer", Sociability),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        StartDating.action_id(),
        normalized_relationship_stat_consideration("performer", "target", Romance),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        StartDating.action_id(),
        normalized_relationship_stat_consideration("target", "performer", Romance),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        StartDating.action_id(),
        normalized_stat_consideration("target", RomancePropensity),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("fire-employee", firing_owner_relationship_cons)

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        TryFormCrush.action_id(),
        normalized_stat_consideration("performer", RomancePropensity),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        FormCrush.action_id(),
        normalized_relationship_stat_consideration("performer", "target", Romance),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        FormCrush.action_id(),
        normalized_stat_consideration("performer", RomancePropensity),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("start-dating", existing_relationship_cons)

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        GetPregnant.action_id(), normalized_stat_consideration("performer", Fertility)
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        GetPregnant.action_id(),
        normalized_stat_consideration("performer", WantForChildren),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        GetPregnant.action_id(),
        normalized_stat_consideration("target", Fertility),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        GetPregnant.action_id(),
        normalized_stat_consideration("target", WantForChildren),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        ProposeMarriage.action_id(),
        normalized_relationship_stat_consideration("performer", "target", Romance),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        ProposeMarriage.action_id(),
        normalized_stat_consideration("performer", Boldness),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        ProposeMarriage.action_id(),
        normalized_stat_consideration("performer", RomancePropensity),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        ProposeMarriage.action_id(),
        normalized_stat_consideration("performer", WantForMarriage),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        GetMarried.action_id(),
        normalized_relationship_stat_consideration("performer", "target", Romance),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        GetMarried.action_id(),
        normalized_relationship_stat_consideration("target", "performer", Romance),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        GetMarried.action_id(),
        normalized_stat_consideration("performer", Luck),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        GetMarried.action_id(),
        normalized_stat_consideration("target", WantForMarriage),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("get-married", marriage_time_dating_consideration)

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration("divorce", divorce_time_married_consideration)

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        Divorce.action_id(),
        invert_cons(
            normalized_relationship_stat_consideration("performer", "target", Romance),
        ),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        Divorce.action_id(),
        invert_cons(
            normalized_stat_consideration("performer", WantForMarriage),
        ),
    )

    sim.world.resources.get_resource(
        ActionConsiderationLibrary
    ).add_success_consideration(
        BreakUp.action_id(),
        invert_cons(
            normalized_relationship_stat_consideration("performer", "target", Romance),
        ),
    )
