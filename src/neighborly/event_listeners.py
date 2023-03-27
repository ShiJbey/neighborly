from neighborly.components import InTheWorkforce, LifeStage, Occupation, Unemployed
from neighborly.components.character import LifeStageType
from neighborly.core.ecs import Active, Event, GameObject
from neighborly.core.life_event import EventHistory, LifeEvent
from neighborly.core.relationship import RelationshipManager
from neighborly.core.status import add_status
from neighborly.events import (
    BecomeYoungAdultEvent,
    DeathEvent,
    DepartEvent,
    JoinSettlementEvent,
)


def add_event_to_personal_history(gameobject: GameObject, event: Event) -> None:
    if isinstance(event, LifeEvent):
        if event_history := gameobject.try_component(EventHistory):
            event_history.append(event)


def on_adult_join_settlement(
    gameobject: GameObject, event: JoinSettlementEvent
) -> None:
    if (
        gameobject.has_component(Active)
        and gameobject.get_component(LifeStage).life_stage >= LifeStageType.YoungAdult
    ):
        add_status(event.character, InTheWorkforce())
        if not event.character.has_component(Occupation):
            add_status(event.character, Unemployed())


def join_workforce_when_young_adult(
    gameobject: GameObject, event: BecomeYoungAdultEvent
) -> None:
    add_status(gameobject, InTheWorkforce())

    if not gameobject.has_component(Occupation):
        add_status(gameobject, Unemployed())


def deactivate_relationships_on_death(
    gameobject: GameObject, event: DeathEvent
) -> None:
    for _, rel_id in gameobject.get_component(RelationshipManager).outgoing.items():
        relationship = gameobject.world.get_gameobject(rel_id)
        if relationship.has_component(Active):
            relationship.remove_component(Active)

    for _, rel_id in gameobject.get_component(RelationshipManager).incoming.items():
        relationship = gameobject.world.get_gameobject(rel_id)
        if relationship.has_component(Active):
            relationship.remove_component(Active)


def deactivate_relationships_on_depart(
    gameobject: GameObject, event: DepartEvent
) -> None:
    for _, rel_id in gameobject.get_component(RelationshipManager).outgoing.items():
        relationship = gameobject.world.get_gameobject(rel_id)
        if relationship.has_component(Active):
            relationship.remove_component(Active)

    for _, rel_id in gameobject.get_component(RelationshipManager).incoming.items():
        relationship = gameobject.world.get_gameobject(rel_id)
        if relationship.has_component(Active):
            relationship.remove_component(Active)
