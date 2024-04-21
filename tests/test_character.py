import pathlib

from neighborly.helpers.character import create_character
from neighborly.loaders import load_characters, load_skills, load_species
from neighborly.plugins import default_traits
from neighborly.simulation import Simulation
from neighborly.systems import InitializeSettlementSystem

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def test_create_character() -> None:
    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")
    load_species(sim, _TEST_DATA_DIR / "species.json")

    default_traits.load_plugin(sim)

    sim.world.system_manager.get_system(InitializeSettlementSystem).set_active(False)

    sim.initialize()

    character = create_character(sim.world, "farmer.female")

    assert character is not None
