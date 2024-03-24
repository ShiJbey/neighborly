# pylint: disable=W0621

"""Tests for Trait-related functionality.

"""

import pytest

from neighborly.components.skills import Skills
from neighborly.components.stats import Stat, Stats
from neighborly.components.traits import Traits
from neighborly.defs.base_types import StatModifierData
from neighborly.defs.trait import DefaultTraitDef
from neighborly.ecs import GameObject
from neighborly.helpers.stats import add_stat, get_stat
from neighborly.helpers.traits import add_trait, has_trait, remove_trait
from neighborly.libraries import TraitLibrary
from neighborly.simulation import Simulation
from neighborly.systems import InitializeSettlementSystem


@pytest.fixture
def test_sim() -> Simulation:
    """Create a test simulation instance."""

    sim = Simulation()

    # Turn off settlement generation. We only care about traits.
    sim.world.systems.get_system(InitializeSettlementSystem).set_active(False)

    library = sim.world.resources.get_resource(TraitLibrary)

    library.add_definition_type(DefaultTraitDef, set_default=True)

    library.add_definition(
        DefaultTraitDef(definition_id="flirtatious", display_name="Flirtatious")
    )

    library.add_definition(
        DefaultTraitDef(
            definition_id="gullible",
            display_name="Gullible",
            stat_modifiers=[StatModifierData(name="sociability", value=3)],
        )
    )

    library.add_definition(
        DefaultTraitDef(
            definition_id="skeptical",
            display_name="Skeptical",
            stat_modifiers=[StatModifierData(name="sociability", value=-3)],
            conflicts_with={"gullible"},
        )
    )

    return sim


def test_trait_instantiation(test_sim: Simulation) -> None:
    """Test that traits are properly initialized by the simulation."""

    # test_sim.initialize()

    library = test_sim.world.resources.get_resource(TraitLibrary)

    trait = library.get_definition("flirtatious")

    assert trait.display_name == "Flirtatious"


def test_add_trait(test_sim: Simulation) -> None:
    """Test that adding a trait makes it visible with has_trait."""

    # Traits are initialized at the start of the simulation
    test_sim.initialize()

    character = GameObject.create_new(
        test_sim.world, components={Traits: {}, Stats: {}, Skills: {}}
    )

    assert has_trait(character, "flirtatious") is False

    add_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is True


def test_remove_trait(test_sim: Simulation) -> None:
    """Test that removing a trait makes it not available to has_trait."""

    # Traits are initialized at the start of the simulation
    test_sim.step()

    character = GameObject.create_new(
        test_sim.world, components={Traits: {}, Stats: {}, Skills: {}}
    )

    assert has_trait(character, "flirtatious") is False

    add_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is True

    remove_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is False


def test_add_remove_trait_effects(test_sim: Simulation) -> None:
    """Test that trait effects are added and removed with the trait."""

    # Traits are initialized at the start of the simulation
    test_sim.initialize()

    farmer = GameObject.create_new(
        test_sim.world, components={Traits: {}, Stats: {}, Skills: {}}
    )

    add_stat(
        farmer,
        Stat(
            name="sociability",
            base_value=0,
            min_value=0,
            max_value=255,
            is_discrete=True,
        ),
    )
    get_stat(farmer, "sociability").base_value = 0

    success = add_trait(farmer, "gullible")

    assert success is True
    assert get_stat(farmer, "sociability").value == 3

    success = remove_trait(farmer, "gullible")

    assert success is True
    assert get_stat(farmer, "sociability").value == 0


def test_try_add_conflicting_trait(test_sim: Simulation) -> None:
    """Test that adding a conflicting trait to a character fails"""

    # Traits are initialized at the start of the simulation
    test_sim.initialize()

    character = GameObject.create_new(
        test_sim.world, components={Traits: {}, Stats: {}, Skills: {}}
    )

    add_stat(
        character,
        Stat(
            name="sociability",
            base_value=0,
            min_value=0,
            max_value=255,
            is_discrete=True,
        ),
    )

    success = add_trait(character, "skeptical")

    assert success is True

    success = add_trait(character, "gullible")

    assert success is False

    success = add_trait(character, "skeptical")

    assert success is False
