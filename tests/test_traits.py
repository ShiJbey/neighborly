"""Tests for Trait-related functionality.

"""

import pathlib

from neighborly.components.skills import Skills
from neighborly.components.stats import Stats
from neighborly.components.traits import Trait, Traits
from neighborly.defs.base_types import TraitDef
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, has_trait, remove_trait
from neighborly.libraries import TraitLibrary
from neighborly.loaders import load_characters, load_skills
from neighborly.plugins import default_definition_types, default_traits
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def test_trait_instantiation() -> None:
    """Test that traits are properly initialized by the simulation."""

    sim = Simulation()

    library = sim.world.resources.get_resource(TraitLibrary)

    library.add_definition(
        TraitDef(definition_id="flirtatious", display_name="Flirtatious")
    )

    # Traits are initialized at the start of the simulation
    sim.initialize()

    trait = library.get_trait("flirtatious")

    assert trait.get_component(Trait).display_name == "Flirtatious"


def test_add_trait() -> None:
    """Test that adding a trait makes it visible with has_trait."""

    sim = Simulation()

    default_definition_types.load_plugin(sim)
    default_traits.load_plugin(sim)

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    # Traits are initialized at the start of the simulation
    sim.initialize()

    character = sim.world.gameobjects.spawn_gameobject(
        components=[Traits(), Stats(), Skills()]
    )

    assert has_trait(character, "flirtatious") is False

    add_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is True


def test_remove_trait() -> None:
    """Test that removing a trait makes it not available to has_trait."""

    sim = Simulation()

    default_definition_types.load_plugin(sim)
    default_traits.load_plugin(sim)

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    # Traits are initialized at the start of the simulation
    sim.step()

    character = sim.world.gameobjects.spawn_gameobject(
        components=[Traits(), Stats(), Skills()]
    )
    assert has_trait(character, "flirtatious") is False

    add_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is True

    remove_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is False


def test_add_remove_trait_effects() -> None:
    """Test that trait effects are added and removed with the trait."""

    sim = Simulation()

    default_definition_types.load_plugin(sim)
    default_traits.load_plugin(sim)

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    # Traits are initialized at the start of the simulation
    sim.initialize()

    farmer = sim.world.gameobjects.spawn_gameobject(
        components=[Traits(), Stats(), Skills()]
    )

    get_stat(farmer, "sociability").base_value = 0

    success = add_trait(farmer, "gullible")

    assert success is True
    assert get_stat(farmer, "sociability").value == 3

    success = remove_trait(farmer, "gullible")

    assert success is True
    assert get_stat(farmer, "sociability").value == 0


def test_try_add_conflicting_trait() -> None:
    """Test that adding a conflicting trait to a character fails"""

    sim = Simulation()

    default_definition_types.load_plugin(sim)
    default_traits.load_plugin(sim)

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    # Traits are initialized at the start of the simulation
    sim.initialize()

    character = sim.world.gameobjects.spawn_gameobject(
        components=[Traits(), Stats(), Skills()]
    )

    success = add_trait(character, "skeptical")

    assert success is True

    success = add_trait(character, "gullible")

    assert success is False

    success = add_trait(character, "skeptical")

    assert success is False
