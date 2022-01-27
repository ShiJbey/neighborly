import esper

from neighborly.core.character.life_event import LifeEvent, register_event_type
from neighborly.core import behavior_utils
from neighborly.core.relationship import Connection


def dating_precondition(world: esper.World, character_id: int, **kwargs) -> bool:
    """Return True if these characters like each other enough to date"""
    other_character_id: int = int(kwargs["other_character"])
    other_character = behavior_utils.get_character(world, other_character_id)
    character = behavior_utils.get_character(world, character_id)

    return (
        character.relationships[other_character_id].has_flags(Connection.LOVE_INTEREST)
        and other_character.relationships[character_id].has_flags(
            Connection.LOVE_INTEREST
        )
        and character.relationships.significant_other is None
        and other_character.relationships.significant_other is None
    )


def dating_posteffects(world: esper.World, character_id: int, **kwargs) -> None:
    """Update the simulation state since these two characters are dating"""
    other_character_id: int = int(kwargs["other_character"])

    # Add dating social practice
    behavior_utils.start_social_practice(
        "dating", world, roles={"partners": [character_id, other_character_id]}
    )

    # Update relationship modifiers
    behavior_utils.add_relationship_modifier(
        world, character_id, other_character_id, "significant other"
    )
    behavior_utils.add_relationship_modifier(
        world, other_character_id, character_id, "significant other"
    )


register_event_type(
    LifeEvent(
        name="Start Dating",
        description="Two characters start a romantic relationship",
        preconditions=dating_precondition,
        post_effects=dating_posteffects,
    )
)


def birth_posteffects(world: esper.World, character_id: int) -> None:
    behavior_utils.start_social_practice(
        "child", world, roles={"subject": [character_id]}
    )


register_event_type(
    LifeEvent(
        name="Start Dating",
        description="Two characters start a romantic relationship",
        preconditions=lambda world, character_id: True,
        post_effects=birth_posteffects,
    )
)
