from neighborly.core.behavior_tree import selector, sequence
from neighborly.core.character import CharacterName, GameCharacter
from neighborly.core.life_event import (
    event_effect,
    LifeEvent,
    event_precondition,
    EventCallbackDatabase,
)
from neighborly.core.ecs import GameObject
from neighborly.core.builtin.events import MarriageEvent
from neighborly.core.builtin.statuses import Adult, InRelationship, Married
from neighborly.core.relationship import Relationship
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.tags import Tag


def can_get_married(gameobject: GameObject, event: LifeEvent) -> bool:
    return gameobject.has_component(Adult) and not gameobject.has_component(
        InRelationship
    )


def marriage_behavior(gameobject: GameObject, event: LifeEvent) -> bool:
    if not isinstance(event, MarriageEvent):
        return False

    character = gameobject.get_component(GameCharacter)

    # Get the partners ID and name
    character_a_id, character_b_id = event.character_ids

    if gameobject.id == character_a_id:
        spouse_id = character_b_id
    else:
        spouse_id = character_a_id

    # Change your last name if your names don't match
    spouse_name = (
        gameobject.world.get_gameobject(spouse_id).get_component(GameCharacter).name
    )
    if spouse_name.surname != character.name.surname:
        character.name = CharacterName(character.name.firstname, spouse_name.surname)

    # Create new Married Status and add it to the game object
    status = Married(spouse_id, str(spouse_name))
    gameobject.add_component(status)

    return True


def load_builtin_behaviors() -> None:
    EventCallbackDatabase.register_precondition(
        "default/can_get_married", can_get_married
    )
    EventCallbackDatabase.register_effect(
        "default/marriage_behavior", marriage_behavior
    )
