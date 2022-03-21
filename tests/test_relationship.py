import pytest

from neighborly.core.relationship import Relationship, RelationshipTag


class FriendTag(RelationshipTag):
    """Indicated a friendship"""

    def __init__(self) -> None:
        super().__init__(
            name="Friend",
            salience_boost=10,
            friendship_increment=1
        )


class EnemyTag(RelationshipTag):
    """Indicated an enmity"""

    def __init__(self) -> None:
        super().__init__(
            name="Enemy",
            salience_boost=10,
            friendship_increment=-1
        )


class AcquaintanceTag(RelationshipTag):
    """Indicated an enmity"""

    def __init__(self) -> None:
        super().__init__(
            name="Acquaintance",
            salience_boost=0.0,
        )


@pytest.fixture
def create_tags():
    RelationshipTag.register_tag(FriendTag())
    RelationshipTag.register_tag(EnemyTag())
    RelationshipTag.register_tag(AcquaintanceTag())


@pytest.mark.usefixtures('create_tags')
def test_load_relationship_tags():
    assert RelationshipTag.get_registered_tag("Acquaintance") is not None
    assert RelationshipTag.get_registered_tag("Friend") is not None
    assert RelationshipTag.get_registered_tag("Enemy") is not None


@pytest.mark.usefixtures('create_tags')
def test_add_remove_modifiers():
    relationship = Relationship(1, 2)

    compatibility_tag = RelationshipTag("Compatibility", friendship_increment=1)

    relationship.add_tag(compatibility_tag)

    assert relationship.has_tags("Compatibility")

    relationship.update()
    
    assert relationship.has_tags("Compatibility")
