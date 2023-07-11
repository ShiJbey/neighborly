import logging

from neighborly import SimDateTime
from neighborly.components.business import InTheWorkforce, Occupation, Unemployed
from neighborly.components.character import LifeStage, LifeStageType
from neighborly.components.role import Roles
from neighborly.core.ecs import Active, Event
from neighborly.core.life_event import EventHistory, EventLog, LifeEvent
from neighborly.core.relationship import RelationshipManager
from neighborly.core.status import add_status
from neighborly.events import (
    BecomeYoungAdultEvent,
    DeathEvent,
    DepartEvent,
    JoinSettlementEvent,
)

_logger = logging.getLogger(__name__)


def add_event_to_personal_history(event: Event) -> None:
    if isinstance(event, LifeEvent):
        event.world.resource_manager.get_resource(EventLog).append(event)
        for gameobject in event.get_affected_gameobjects():
            if event_history := gameobject.try_component(EventHistory):
                event_history.append(event)


def on_adult_join_settlement(event: JoinSettlementEvent) -> None:
    if (
        event.character.has_component(Active)
        and event.character.get_component(LifeStage).life_stage
        >= LifeStageType.YoungAdult
    ):
        date = event.world.resource_manager.get_resource(SimDateTime)
        add_status(event.character, InTheWorkforce(year_created=date.year))
        if roles := event.character.try_component(Roles):
            if len(roles.get_roles_of_type(Occupation)) == 0:
                add_status(event.character, Unemployed(year_created=date.year))


def join_workforce_when_young_adult(event: BecomeYoungAdultEvent) -> None:
    date = event.world.resource_manager.get_resource(SimDateTime)
    add_status(event.character, InTheWorkforce(year_created=date.year))

    if roles := event.character.try_component(Roles):
        if len(roles.get_roles_of_type(Occupation)) == 0:
            add_status(event.character, Unemployed(year_created=date.year))


def deactivate_relationships_on_death(event: DeathEvent) -> None:
    for _, relationship in event.character.get_component(
        RelationshipManager
    ).outgoing.items():
        relationship.deactivate()

    for _, relationship in event.character.get_component(
        RelationshipManager
    ).incoming.items():
        relationship.deactivate()


def deactivate_relationships_on_depart(event: DepartEvent) -> None:
    for character in event.characters:
        for _, relationship in character.get_component(
            RelationshipManager
        ).outgoing.items():
            relationship.deactivate()

        for _, relationship in character.get_component(
            RelationshipManager
        ).incoming.items():
            relationship.deactivate()


def log_life_event(event: Event) -> None:
    if isinstance(event, LifeEvent):
        _logger.info(str(event))
