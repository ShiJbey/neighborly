from neighborly.core.relationship import RelationshipTag


class FriendTag(RelationshipTag):
    """Indicates a friendship"""

    def __init__(self) -> None:
        super().__init__(
            name="Friend",
            salience_boost=30,
            friendship_increment=1
        )
