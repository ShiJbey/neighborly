"""Default responses to various life events.

Responses implement relationship and personal stat changes using event listeners.

"""

from typing import cast

from neighborly.components.relationship import Reputation, Romance
from neighborly.ecs import Event, GameObject
from neighborly.helpers.relationship import get_relationship
from neighborly.plugins.default_events import (
    DatingBreakUpEvent,
    DivorceEvent,
    MarriageProposalRejectionEvent,
    RejectDatingProposalEvent,
)
from neighborly.simulation import Simulation


def break_up_response(event: Event) -> None:
    """Listens for break ups and updates relationships."""

    if isinstance(event, DatingBreakUpEvent):

        get_relationship(event.partner, event.initiator).get_component(
            Romance
        ).stat.base_value -= 15
        get_relationship(event.partner, event.initiator).get_component(
            Reputation
        ).stat.base_value -= 15


def divorce_response(event: Event) -> None:
    """Listens for divorces and updates relationships."""

    if isinstance(event, DivorceEvent):

        get_relationship(event.partner, event.initiator).get_component(
            Romance
        ).stat.base_value -= 20
        get_relationship(event.partner, event.initiator).get_component(
            Reputation
        ).stat.base_value -= 25


def dating_proposal_rejection_response(event: Event) -> None:
    """Listens for proposal rejections."""

    performer = cast(GameObject, event.data["performer"])
    target = cast(GameObject, event.data["target"])

    get_relationship(target, performer).get_component(Romance).stat.base_value -= 5


def marriage_proposal_rejection_response(event: Event) -> None:
    """Listens for proposal rejections."""

    performer = cast(GameObject, event.data["performer"])
    target = cast(GameObject, event.data["target"])

    get_relationship(target, performer).get_component(Romance).stat.base_value -= 20
    get_relationship(target, performer).get_component(Reputation).stat.base_value -= 15


def load_plugin(sim: Simulation) -> None:
    """Load responses into a simulation."""

    sim.world.events.on_event(
        DatingBreakUpEvent.event_name(),
        break_up_response,
    )

    sim.world.events.on_event(
        DivorceEvent.event_name(),
        divorce_response,
    )

    sim.world.events.on_event(
        RejectDatingProposalEvent.event_name(),
        dating_proposal_rejection_response,
    )

    sim.world.events.on_event(
        MarriageProposalRejectionEvent.event_name(),
        marriage_proposal_rejection_response,
    )
