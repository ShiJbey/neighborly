from neighborly.core.relationship import RelationshipModifier


class FriendModifier(RelationshipModifier):
    """Indicates a friendship"""

    def __init__(self) -> None:
        super().__init__(name="Friend", salience_boost=30, friendship_increment=1)
