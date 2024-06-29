# pylint: disable=redefined-outer-name, disable=W0621
"""Test Relationship Components, Systems, and Helper Functions.

"""

import pathlib

import pytest

from neighborly.components.stats import StatModifierType
from neighborly.components.traits import Trait
from neighborly.effects.effects import AddRelationshipModifier, AddStatModifier
from neighborly.effects.modifiers import RelationshipModifierDir
from neighborly.helpers.character import create_character
from neighborly.helpers.relationship import (
    add_relationship,
    get_relationship,
    has_relationship,
)
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, remove_trait
from neighborly.libraries import CharacterLibrary, TraitLibrary
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_settlements,
    load_skills,
    load_species,
)
from neighborly.plugins import default_character_names, default_settlement_names
from neighborly.simulation import Simulation

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


@pytest.fixture
def sim() -> Simulation:
    """Create sample simulation to use for test cases"""
    simulation = Simulation()

    load_districts(simulation, _DATA_DIR / "districts.json")
    load_settlements(simulation, _DATA_DIR / "settlements.json")
    load_businesses(simulation, _DATA_DIR / "businesses.json")
    load_characters(simulation, _DATA_DIR / "characters.json")
    load_job_roles(simulation, _DATA_DIR / "job_roles.json")
    load_skills(simulation, _DATA_DIR / "skills.json")
    load_species(simulation, _DATA_DIR / "species.json")

    # default_traits.load_plugin(simulation)
    default_character_names.load_plugin(simulation)
    default_settlement_names.load_plugin(simulation)

    simulation.world.resources.get_resource(TraitLibrary).add_trait(
        Trait(
            definition_id="gullible",
            name="Gullible",
            description="",
            effects=[
                AddRelationshipModifier(
                    direction=RelationshipModifierDir.OUTGOING,
                    description="",
                    preconditions=[],
                    effects=[
                        AddStatModifier(
                            stat="reputation",
                            value=10,
                            modifier_type=StatModifierType.FLAT,
                        )
                    ],
                )
            ],
            conflicting_traits=set(),
        )
    )

    # IMPORTANT: Stop character from generating with traits
    simulation.world.resources.get_resource(CharacterLibrary).get_definition(
        "base_character"
    ).traits.clear()

    simulation.initialize()

    return simulation


def test_get_relationship(sim: Simulation) -> None:
    """Test that get_relationship creates new relationship if one does not exist."""

    a = create_character(sim.world, "base_character.female")
    b = create_character(sim.world, "base_character.male")

    assert has_relationship(a, b) is False
    assert has_relationship(b, a) is False

    a_to_b = get_relationship(a, b)

    assert has_relationship(a, b) is True
    assert has_relationship(b, a) is False

    b_to_a = get_relationship(b, a)

    assert has_relationship(a, b) is True
    assert has_relationship(b, a) is True

    assert id(a_to_b) != id(b_to_a)

    a_to_b_again = get_relationship(a, b)

    assert id(a_to_b) == id(a_to_b_again)


def test_add_relationship(sim: Simulation) -> None:
    """Test that adding a relationship create a new relationship or returns the old"""

    a = create_character(sim.world, "base_character.male")
    b = create_character(sim.world, "base_character.female")

    assert has_relationship(a, b) is False
    assert has_relationship(b, a) is False

    add_relationship(a, b)

    assert has_relationship(a, b) is True
    assert has_relationship(b, a) is False


def test_trait_with_social_rules(sim: Simulation) -> None:
    """Test traits that apply social rules"""

    farmer = create_character(sim.world, "farmer.female")
    merchant = create_character(sim.world, "merchant.male")
    noble = create_character(sim.world, "nobility.female")

    rel_to_noble = add_relationship(farmer, noble)

    assert get_stat(rel_to_noble, "reputation").value == 0

    add_trait(farmer, "gullible")

    assert get_stat(rel_to_noble, "reputation").value == 10

    rel = add_relationship(farmer, merchant)

    assert get_stat(rel, "reputation").value == 10

    remove_trait(farmer, "gullible")

    assert get_stat(rel, "reputation").value == 0
    assert get_stat(rel_to_noble, "reputation").value == 0
