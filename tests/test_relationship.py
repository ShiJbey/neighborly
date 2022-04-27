import pytest

from neighborly.core.relationship import Relationship, RelationshipModifier


class FriendModifier(RelationshipModifier):
    """Indicated a friendship"""

    def __init__(self) -> None:
        super().__init__(
            name="Friend",
            salience_boost=10,
            friendship_increment=1
        )


class EnemyModifier(RelationshipModifier):
    """Indicated an enmity"""

    def __init__(self) -> None:
        super().__init__(
            name="Enemy",
            salience_boost=10,
            friendship_increment=-1
        )


class AcquaintanceModifier(RelationshipModifier):
    """Indicated an enmity"""

    def __init__(self) -> None:
        super().__init__(
            name="Acquaintance",
            salience_boost=0.0,
        )


@pytest.fixture
def create_tags():
    RelationshipModifier.register_tag(FriendModifier())
    RelationshipModifier.register_tag(EnemyModifier())
    RelationshipModifier.register_tag(AcquaintanceModifier())


@pytest.mark.usefixtures('create_tags')
def test_load_relationship_tags():
    assert RelationshipModifier.get_tag("Acquaintance") is not None
    assert RelationshipModifier.get_tag("Friend") is not None
    assert RelationshipModifier.get_tag("Enemy") is not None


@pytest.mark.usefixtures('create_tags')
def test_add_remove_modifiers():
    relationship = Relationship(1, 2)

    compatibility_tag = RelationshipModifier("Compatibility", friendship_increment=1)

    relationship.add_modifier(compatibility_tag)

    assert relationship.has_modifier("Compatibility")

    relationship.update()

    assert relationship.has_modifier("Compatibility")
