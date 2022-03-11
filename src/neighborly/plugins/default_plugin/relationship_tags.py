from neighborly.core.relationship import RelationshipTag


class FriendTag(RelationshipTag):
    """Indicated a friendship"""

    def __init__(self) -> None:
        super().__init__(
            name="Friend",
            automatic=True,
            salience_boost=30,
            friendship_increment=1
        )
