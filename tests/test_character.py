"""Test character-related functionality.

"""

import pathlib

import pytest

from neighborly.components.character import (
    HeadOfHousehold,
    Household,
    MemberOfHousehold,
)
from neighborly.helpers.character import (
    add_character_to_household,
    create_character,
    create_household,
    remove_character_from_household,
    set_household_head,
)
from neighborly.loaders import load_characters, load_skills, load_species
from neighborly.plugins import default_character_names, default_traits
from neighborly.plugins.actions import GetMarried
from neighborly.simulation import Simulation
from neighborly.systems import InitializeSettlementSystem

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


@pytest.fixture
def sim() -> Simulation:

    simulation = Simulation()

    load_characters(simulation, _DATA_DIR / "characters.json")
    load_skills(simulation, _DATA_DIR / "skills.json")
    load_species(simulation, _DATA_DIR / "species.json")

    default_traits.load_plugin(simulation)
    default_character_names.load_plugin(simulation)

    simulation.world.system_manager.get_system(InitializeSettlementSystem).set_active(
        False
    )

    simulation.initialize()

    return simulation


def test_create_character(sim: Simulation) -> None:
    """Test character creation."""

    character = create_character(sim.world, "farmer.female")

    assert character is not None


def test_set_household_head(sim: Simulation) -> None:
    """Test that household leadership changes hands properly"""

    character_a = create_character(sim.world, "farmer.female")

    household = create_household(sim.world)

    assert character_a.has_component(HeadOfHousehold) is False
    assert character_a.has_component(MemberOfHousehold) is False

    set_household_head(household, character_a)

    assert household.get_component(Household).head == character_a
    assert character_a.has_component(HeadOfHousehold) is True
    assert character_a.has_component(MemberOfHousehold) is False

    character_b = create_character(sim.world, "farmer.female")

    assert character_b.has_component(HeadOfHousehold) is False
    assert character_b.has_component(MemberOfHousehold) is False

    set_household_head(household, character_b)

    assert household.get_component(Household).head == character_b
    assert character_b.has_component(HeadOfHousehold) is True
    assert character_a.has_component(HeadOfHousehold) is False

    set_household_head(household, None)

    assert household.get_component(Household).head is None
    assert character_b.has_component(HeadOfHousehold) is False
    assert character_a.has_component(HeadOfHousehold) is False


def test_add_character_to_household(sim: Simulation) -> None:
    """Test adding characters to households."""

    character_a = create_character(sim.world, "farmer.female")
    character_b = create_character(sim.world, "farmer.female")
    household = create_household(sim.world)

    assert len(household.get_component(Household).members) == 0
    assert character_a.has_component(MemberOfHousehold) is False
    assert character_b.has_component(MemberOfHousehold) is False

    add_character_to_household(household, character_a)
    add_character_to_household(household, character_b)

    assert len(household.get_component(Household).members) == 2
    assert character_a.has_component(MemberOfHousehold) is True
    assert character_b.has_component(MemberOfHousehold) is True


def test_remove_character_from_household(sim: Simulation) -> None:
    """Test removing characters from households."""

    character_a = create_character(sim.world, "farmer.female")
    character_b = create_character(sim.world, "farmer.female")
    household = create_household(sim.world)

    assert len(household.get_component(Household).members) == 0
    assert character_a.has_component(MemberOfHousehold) is False
    assert character_b.has_component(MemberOfHousehold) is False

    add_character_to_household(household, character_a)
    add_character_to_household(household, character_b)

    assert len(household.get_component(Household).members) == 2
    assert character_a.has_component(MemberOfHousehold) is True
    assert character_b.has_component(MemberOfHousehold) is True

    remove_character_from_household(household, character_a)
    remove_character_from_household(household, character_b)

    assert len(household.get_component(Household).members) == 0
    assert character_a.has_component(MemberOfHousehold) is False
    assert character_b.has_component(MemberOfHousehold) is False


def test_marriage_both_heads(sim: Simulation) -> None:
    """Test marriage between household heads."""

    character_a = create_character(sim.world, "farmer.female")
    other_a = create_character(sim.world, "farmer.female")
    character_b = create_character(sim.world, "farmer.female")
    other_b = create_character(sim.world, "farmer.female")
    household_a = create_household(sim.world)
    household_b = create_household(sim.world)

    set_household_head(household_a, character_a)
    add_character_to_household(household_a, character_a)
    add_character_to_household(household_a, other_a)

    set_household_head(household_b, character_b)
    add_character_to_household(household_b, character_b)
    add_character_to_household(household_b, other_b)

    GetMarried(character_a, character_b).execute()

    assert household_b.is_active is False

    household_component_a = household_a.get_component(Household)

    assert len(household_component_a.members) == 4
    assert household_component_a.head == character_a
    assert character_b in household_component_a.members
    assert other_b in household_component_a.members
    assert character_b.get_component(MemberOfHousehold).household == household_a
    assert other_b.get_component(MemberOfHousehold).household == household_a


def test_marriage_from_head_to_member(sim: Simulation) -> None:
    """Test marriage where the initiator is a household head and the partner is not."""

    character_a = create_character(sim.world, "farmer.female")
    other_a = create_character(sim.world, "farmer.female")
    character_b = create_character(sim.world, "farmer.female")
    other_b = create_character(sim.world, "farmer.female")
    household_a = create_household(sim.world)
    household_b = create_household(sim.world)

    set_household_head(household_a, character_a)
    add_character_to_household(household_a, character_a)
    add_character_to_household(household_a, other_a)

    add_character_to_household(household_b, character_b)
    add_character_to_household(household_b, other_b)

    GetMarried(character_a, character_b).execute()

    assert household_b.is_active is True
    assert len(household_b.get_component(Household).members) == 1

    household_component_a = household_a.get_component(Household)

    assert len(household_component_a.members) == 3
    assert household_component_a.head == character_a
    assert character_b in household_component_a.members
    assert other_b not in household_component_a.members
    assert character_b.get_component(MemberOfHousehold).household == household_a
    assert other_b.get_component(MemberOfHousehold).household == household_b


def test_marriage_from_member_to_head(sim: Simulation) -> None:
    """Test marriage where the initiator is not a household head and the partner is."""

    character_a = create_character(sim.world, "farmer.female")
    other_a = create_character(sim.world, "farmer.female")
    character_b = create_character(sim.world, "farmer.female")
    other_b = create_character(sim.world, "farmer.female")
    household_a = create_household(sim.world)
    household_b = create_household(sim.world)

    add_character_to_household(household_a, character_a)
    add_character_to_household(household_a, other_a)

    set_household_head(household_b, character_b)
    add_character_to_household(household_b, character_b)
    add_character_to_household(household_b, other_b)

    GetMarried(character_a, character_b).execute()

    new_household = character_a.get_component(MemberOfHousehold).household

    assert new_household != household_a
    assert new_household != household_b

    assert household_a.is_active is True
    assert household_b.is_active is False

    assert len(household_a.get_component(Household).members) == 1
    assert len(new_household.get_component(Household).members) == 3

    assert new_household.get_component(Household).head == character_a
    assert character_b in new_household.get_component(Household).members
    assert other_b in new_household.get_component(Household).members
    assert other_a in household_a.get_component(Household).members
    assert character_a.get_component(MemberOfHousehold).household == new_household
    assert character_b.get_component(MemberOfHousehold).household == new_household
    assert other_b.get_component(MemberOfHousehold).household == new_household


def test_marriage_from_member_to_member(sim: Simulation) -> None:
    """Test marriage where neither character is the head of a household."""

    character_a = create_character(sim.world, "farmer.female")
    other_a = create_character(sim.world, "farmer.female")
    character_b = create_character(sim.world, "farmer.female")
    other_b = create_character(sim.world, "farmer.female")
    household_a = create_household(sim.world)
    household_b = create_household(sim.world)

    add_character_to_household(household_a, character_a)
    add_character_to_household(household_a, other_a)

    add_character_to_household(household_b, character_b)
    add_character_to_household(household_b, other_b)

    GetMarried(character_a, character_b).execute()

    new_household = character_a.get_component(MemberOfHousehold).household

    assert new_household != household_a
    assert new_household != household_b

    assert household_a.is_active is True
    assert household_b.is_active is True

    assert len(household_a.get_component(Household).members) == 1
    assert len(household_b.get_component(Household).members) == 1
    assert len(new_household.get_component(Household).members) == 2

    assert new_household.get_component(Household).head == character_a
    assert character_b in new_household.get_component(Household).members
    assert other_b in household_b.get_component(Household).members
    assert other_a in household_a.get_component(Household).members
    assert character_a.get_component(MemberOfHousehold).household == new_household
    assert character_b.get_component(MemberOfHousehold).household == new_household
    assert other_b.get_component(MemberOfHousehold).household == household_b
    assert other_a.get_component(MemberOfHousehold).household == household_a
