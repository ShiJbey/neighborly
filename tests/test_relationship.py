import pytest
import yaml

from neighborly.core.relationship import Relationship, load_relationship_tags, RelationshipTag


@pytest.fixture
def load_tags():
    tag_defs = """
    RelationshipTags:
      - name: Acquaintance
        friendship: 1
        requirements: "friendship < 7 AND friendship > -7"
      - name: Friend
        salience: 20
        requirements: "friendship > 15"
      - name: Enemy
        salience: 20
        requirements: "friendship < -10"
      - name: Best Friend
        salience: 30
        requirements: "friendship > 40"
    """

    data = yaml.safe_load(tag_defs)
    load_relationship_tags(data['RelationshipTags'])


@pytest.mark.usefixtures('load_tags')
def test_load_relationship_tags():
    assert Relationship.get_tag("Acquaintance") is not None
    assert Relationship.get_tag("Friend") is not None
    assert Relationship.get_tag("Enemy") is not None
    assert Relationship.get_tag("Best Friend") is not None


@pytest.mark.usefixtures('load_tags')
def test_add_remove_modifiers():
    relationship = Relationship(1, 2)

    relationship.update()

    assert relationship.has_tags("Acquaintance")

    instant_friend_mod = RelationshipTag("Instant Best Friends", friendship=40)

    relationship.add_tag(instant_friend_mod)

    relationship.update()

    assert relationship.has_tags("Friend") is True
