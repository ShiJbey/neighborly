from neighborly.ai import behavior_utils
from neighborly.core.character.life_event import LifeEvent, register_event_type
from neighborly.core.ecs import World
from neighborly.core.social_network import RelationshipNetwork


def dating_precondition(world: World, character_id: int, **kwargs) -> bool:
    """Return True if these characters like each other enough to date"""
    other_character_id: int = int(kwargs["other_character"])
    relationship_net = world.get_resource(RelationshipNetwork)

    return (
            relationship_net.get_connection(character_id, other_character_id).has_tags("Love Interest") and
            relationship_net.get_connection(other_character_id, character_id).has_tags("Love Interest") and
            len(relationship_net.get_all_relationships_with_tags(character_id, "Significant Other")) == 0 and
            len(relationship_net.get_all_relationships_with_tags(other_character_id, "Significant Other")) == 0
    )


def dating_post_effects(world: World, character_id: int, **kwargs) -> None:
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
        post_effects=dating_post_effects,
    )
)


def birth_post_effects(world: World, character_id: int) -> None:
    behavior_utils.start_social_practice(
        "child", world, roles={"subject": [character_id]}
    )


register_event_type(
    LifeEvent(
        name="Start Dating",
        description="Two characters start a romantic relationship",
        preconditions=lambda world, character_id: True,
        post_effects=birth_post_effects,
    )
)
