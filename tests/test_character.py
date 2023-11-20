import pathlib

from neighborly.helpers.character import create_character
from neighborly.loaders import load_characters, load_skills
from neighborly.plugins import default_traits
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def test_create_character() -> None:
    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    character = create_character(sim.world, "farmer")

    assert character is not None
