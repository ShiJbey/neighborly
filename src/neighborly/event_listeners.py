from neighborly.components.business import InTheWorkforce, Occupation, Unemployed
from neighborly.components.character import LifeStage, LifeStageType
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


def add_event_to_personal_history(event: Event) -> None:
    if isinstance(event, LifeEvent):
        event.world.resource_manager.get_resource(EventLog).append(event)
        for role in event.roles:
            if event_history := role.gameobject.try_component(EventHistory):
                event_history.append(event)


def on_adult_join_settlement(event: JoinSettlementEvent) -> None:
    if (
        event.character.has_component(Active)
        and event.character.get_component(LifeStage).life_stage
        >= LifeStageType.YoungAdult
    ):
        add_status(event.character, InTheWorkforce())
        if not event.character.has_component(Occupation):
            add_status(event.character, Unemployed())


def join_workforce_when_young_adult(event: BecomeYoungAdultEvent) -> None:
    add_status(event.character, InTheWorkforce())

    if not event.character.has_component(Occupation):
        add_status(event.character, Unemployed())


def deactivate_relationships_on_death(event: DeathEvent) -> None:
    for _, relationship in event.character.get_component(
        RelationshipManager
    ).outgoing.items():
        if relationship.has_component(Active):
            relationship.remove_component(Active)

    for _, relationship in event.character.get_component(
        RelationshipManager
    ).incoming.items():
        if relationship.has_component(Active):
            relationship.remove_component(Active)


def deactivate_relationships_on_depart(event: DepartEvent) -> None:
    for character in event.characters:
        for _, relationship in character.get_component(
            RelationshipManager
        ).outgoing.items():
            if relationship.has_component(Active):
                relationship.remove_component(Active)

        for _, relationship in character.get_component(
            RelationshipManager
        ).incoming.items():
            if relationship.has_component(Active):
                relationship.remove_component(Active)


def print_life_events(event: Event) -> None:
    if isinstance(event, LifeEvent):
        print(str(event))
