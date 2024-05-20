"""Default responses to various life events.

Responses implement relationship and personal stat changes using event listeners.

"""

from neighborly.components.relationship import Reputation, Romance
from neighborly.ecs import IEvent
from neighborly.helpers.relationship import get_relationship
from neighborly.plugins.default_events import DatingBreakUpEvent, DivorceEvent
from neighborly.simulation import Simulation


def break_up_response(event: IEvent) -> None:
    """Listens for break ups and updates relationships."""

    if isinstance(event, DatingBreakUpEvent):

        get_relationship(event.partner, event.initiator).get_component(
            Romance
        ).stat.base_value -= 15
        get_relationship(event.partner, event.initiator).get_component(
            Reputation
        ).stat.base_value -= 15


def divorce_response(event: IEvent) -> None:
    """Listens for divorces and updates relationships."""

    if isinstance(event, DivorceEvent):

        get_relationship(event.partner, event.initiator).get_component(
            Romance
        ).stat.base_value -= 20
        get_relationship(event.partner, event.initiator).get_component(
            Reputation
        ).stat.base_value -= 25


def load_plugin(sim: Simulation) -> None:
    """Load responses into a simulation."""

    sim.world.events.on_event("dating_break_up", break_up_response)
    sim.world.events.on_event("divorce", divorce_response)
