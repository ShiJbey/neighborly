"""Test character-related functionality.

"""

import pathlib

from neighborly.helpers.character import create_character
from neighborly.loaders import load_characters, load_skills, load_species
from neighborly.plugins import default_character_names, default_traits
from neighborly.simulation import Simulation
from neighborly.systems import InitializeSettlementSystem

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


def test_create_character() -> None:
    """Test character creation."""

    sim = Simulation()

    load_characters(sim, _DATA_DIR / "characters.json")
    load_skills(sim, _DATA_DIR / "skills.json")
    load_species(sim, _DATA_DIR / "species.json")

    default_traits.load_plugin(sim)
    default_character_names.load_plugin(sim)

    sim.world.system_manager.get_system(InitializeSettlementSystem).set_active(False)

    sim.initialize()

    character = create_character(sim.world, "farmer.female")

    assert character is not None
