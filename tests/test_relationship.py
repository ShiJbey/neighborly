import pytest

from neighborly.core.relationship import (
    Relationship,
    RelationshipGraph,
    RelationshipModifier,
    RelationshipTag,
)


class FriendModifier(RelationshipModifier):
    """Indicated a friendship"""

    def __init__(self) -> None:
        super().__init__(name="Friend", salience_boost=10, friendship_increment=1)


class EnemyModifier(RelationshipModifier):
    """Indicated an enmity"""

    def __init__(self) -> None:
        super().__init__(name="Enemy", salience_boost=10, friendship_increment=-1)


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


@pytest.mark.usefixtures("create_tags")
def test_load_relationship_tags():
    assert RelationshipModifier.get_tag("Acquaintance") is not None
    assert RelationshipModifier.get_tag("Friend") is not None
    assert RelationshipModifier.get_tag("Enemy") is not None


@pytest.mark.usefixtures("create_tags")
def test_add_remove_modifiers():
    relationship = Relationship(1, 2)

    compatibility_tag = RelationshipModifier("Compatibility", friendship_increment=1)

    relationship.add_modifier(compatibility_tag)

    assert relationship.has_modifier("Compatibility")

    relationship.update()

    assert relationship.has_modifier("Compatibility")


def test_relationship_network():
    # Create characters as ints
    homer = 0
    lisa = 1
    krusty = 2
    bart = 3
    maggie = 4

    # Construct the social graph
    social_graph = RelationshipGraph()

    homer_to_lisa_rel = Relationship(homer, lisa)
    lisa_to_homer_rel = Relationship(lisa, homer)

    social_graph.add_connection(homer, lisa, homer_to_lisa_rel)
    social_graph.add_connection(lisa, homer, lisa_to_homer_rel)

    assert social_graph.get_connection(homer, lisa) == homer_to_lisa_rel

    social_graph.add_connection(homer, bart, Relationship(homer, bart))
    social_graph.add_connection(bart, krusty, Relationship(bart, krusty))
    social_graph.add_connection(krusty, bart, Relationship(krusty, bart))

    social_graph.add_connection(lisa, bart, Relationship(lisa, bart))
    social_graph.get_connection(lisa, bart).add_tags(
        RelationshipTag.Brother | RelationshipTag.Sibling
    )

    social_graph.add_connection(lisa, maggie, Relationship(lisa, maggie))
    social_graph.get_connection(lisa, maggie).add_tags(
        RelationshipTag.Sister | RelationshipTag.Sibling
    )

    assert social_graph.has_connection(homer, krusty) is False
    assert social_graph.has_connection(lisa, homer) is True
    assert social_graph.has_connection(bart, lisa) is False

    social_graph.get_connection(homer, lisa).add_tags(RelationshipTag.Daughter)
    social_graph.get_connection(homer, lisa).has_tags(RelationshipTag.Daughter)

    assert (
        len(social_graph.get_all_relationships_with_tags(lisa, RelationshipTag.Sibling))
        == 2
    )

    social_graph.remove_node(homer)

    assert social_graph.has_connection(lisa, homer) is False
    assert social_graph.has_connection(homer, lisa) is False
    assert social_graph.has_connection(homer, bart) is False
