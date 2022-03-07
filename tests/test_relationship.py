import pytest

from neighborly.core.relationship import Relationship, RelationshipTag


# @pytest.fixture
# def load_tags():
#     tag_defs = """
#     RelationshipTags:
#       - name: Acquaintance
#         friendship: 1
#         requirements: "friendship < 7 AND friendship > -7"
#       - name: Friend
#         salience: 20
#         requirements: "friendship > 15"
#       - name: Enemy
#         salience: 20
#         requirements: "friendship < -10"
#       - name: Best Friend
#         salience: 30
#         requirements: "friendship > 40"
#     """
#
#     data = yaml.safe_load(tag_defs)
#     load_relationship_tags(data['RelationshipTags'])
#
#


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
            salience_boost=10,
            friendship_increment=1
        )


class EnemyTag(RelationshipTag):
    """Indicated an enmity"""

    def __init__(self) -> None:
        def req(relationship: Relationship) -> bool:
            """Relationship Tag requirement"""
            return relationship.friendship < -15

        super().__init__(
            name="Enemy",
            automatic=True,
            requirements=[req],
            salience_boost=10,
            friendship_increment=-1
        )


class AcquaintanceTag(RelationshipTag):
    """Indicated an enmity"""

    def __init__(self) -> None:
        def req(relationship: Relationship) -> bool:
            """Relationship Tag requirement"""
            return -7 < relationship.friendship < 7

        super().__init__(
            name="Acquaintance",
            automatic=True,
            requirements=[req],
            salience_boost=0.0,
        )


@pytest.fixture
def create_tags():
    Relationship.register_tag(FriendTag())
    Relationship.register_tag(EnemyTag())
    Relationship.register_tag(AcquaintanceTag())


@pytest.mark.usefixtures('create_tags')
def test_load_relationship_tags():
    assert Relationship.get_tag("Acquaintance") is not None
    assert Relationship.get_tag("Friend") is not None
    assert Relationship.get_tag("Enemy") is not None


@pytest.mark.usefixtures('create_tags')
def test_add_remove_modifiers():
    relationship = Relationship(1, 2)

    relationship.update()

    assert relationship.has_tags("Acquaintance")

    compatibility_tag = RelationshipTag("Compatibility", friendship_increment=1)

    relationship.add_tag(compatibility_tag)

    assert relationship.has_tags("Compatibility")
    relationship.update()
    assert relationship.has_tags("Compatibility")
