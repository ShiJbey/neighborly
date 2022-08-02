from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject
from neighborly.core.life_event import LifeEvent, event_precondition
from neighborly.core.relationship import RelationshipTag
from neighborly.core.utils.utilities import clamp
from neighborly.plugins.talktown.personality import BigFivePersonality


# =========================================
# PRECONDITIONS
# =========================================


@event_precondition("will_engage_in_social_interaction")
def will_instigate_social_interaction(gameobject: GameObject, event: LifeEvent) -> bool:
    character = gameobject.get_component(GameCharacter)
    personality = gameobject.get_component(BigFivePersonality)

    if character.age < 5:
        return False

    return False


def _get_extroversion_component_to_chance_of_social_interaction(
    personality: BigFivePersonality, floor: float, cap: float
) -> float:
    """Return the effect of this person's extroversion on the chance of instigating social interaction."""
    return clamp(personality.extroversion, floor, cap)


def _get_openness_component_to_chance_of_social_interaction(
    personality: BigFivePersonality, floor: float, cap: float
) -> float:
    """Return the effect of this person's openness on the chance of instigating social interaction."""
    return clamp(personality.openness, floor, cap)


def _get_friendship_component_to_chance_of_social_interaction(
    character: GameCharacter,
    other_character_id: int,
    friend_boost: float,
    best_friend_boost: float,
) -> float:
    """Return the effect of an existing friendship on the chance of instigating social interaction."""
    friendship_component = 0.0
    relationship = character.gameobject.get_component(
        RelationshipManager
    ).get_relationship(other_character_id)

    if relationship is None:
        return friendship_component

    if relationship.has_tags(RelationshipTag.Friend):
        friendship_component += friend_boost

    if relationship.has_tags(RelationshipTag.BestFriend):
        friendship_component += best_friend_boost

    return friendship_component
