import pytest
import yaml

from neighborly.core.relationship import Relationship, load_relationship_tags, RelationshipTag
from neighborly.core.social_network import RelationshipNetwork


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


def test_relationship_network():
    # Create characters as ints
    homer = 0
    lisa = 1
    krusty = 2
    bart = 3
    maggie = 4

    # Construct the social graph
    social_graph = RelationshipNetwork()

    homer_to_lisa_rel = Relationship(homer, lisa)
    lisa_to_homer_rel = Relationship(lisa, homer)

    social_graph.add_connection(homer, lisa, homer_to_lisa_rel)
    social_graph.add_connection(lisa, homer, lisa_to_homer_rel)

    assert social_graph.get_connection(homer, lisa) == homer_to_lisa_rel

    social_graph.add_connection(homer, bart, Relationship(homer, bart))
    social_graph.add_connection(bart, krusty, Relationship(bart, krusty))
    social_graph.add_connection(krusty, bart, Relationship(krusty, bart))

    social_graph.add_connection(lisa, bart, Relationship(lisa, bart))
    social_graph.get_connection(lisa, bart).add_tag(RelationshipTag("Sibling"))

    social_graph.add_connection(lisa, maggie, Relationship(lisa, maggie))
    social_graph.get_connection(lisa, maggie).add_tag(RelationshipTag("Sibling"))

    assert social_graph.has_connection(homer, krusty) is False
    assert social_graph.has_connection(lisa, homer) is True
    assert social_graph.has_connection(bart, lisa) is False

    social_graph.get_connection(homer, lisa).add_tag(RelationshipTag("Father"))
    social_graph.get_connection(homer, lisa).has_tags("Father")

    assert len(social_graph.get_all_relationships_with_tags(lisa, "Sibling")) == 2
