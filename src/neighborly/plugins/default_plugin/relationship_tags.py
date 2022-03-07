from neighborly.core.relationship import Relationship, RelationshipTag


class FriendTag(RelationshipTag):
    """Indicated a friendship"""

    def __init__(self) -> None:
        def req(relationship: Relationship) -> bool:
            """Relationship Tag requirement"""
            return relationship.friendship > 15

        super().__init__(
            name="Friend",
            automatic=True,
            requirements=[req],
            salience_boost=30,
            friendship_increment=1
        )
