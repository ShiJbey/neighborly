from neighborly.core.relationship import RelationshipModifier


def create_friend_modifier() -> RelationshipModifier:
    return RelationshipModifier(
        name="Friend",
        description="These characters are firends",
        salience_boost=30,
        friendship_increment=1,
    )
