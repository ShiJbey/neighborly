# pylint: disable=W0621

import pathlib

import pytest

from neighborly.components.settlement import Settlement
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_settlements,
    load_skills,
    load_species,
)
from neighborly.plugins import (
    default_character_names,
    default_settlement_names,
    default_traits,
)
from neighborly.simulation import Simulation

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


@pytest.fixture
def test_sim() -> Simulation:
    """Create a simulation instance for tests."""

    sim = Simulation()

    load_districts(sim, _DATA_DIR / "districts.json")
    load_settlements(sim, _DATA_DIR / "settlements.json")
    load_businesses(sim, _DATA_DIR / "businesses.json")
    load_characters(sim, _DATA_DIR / "characters.json")
    load_job_roles(sim, _DATA_DIR / "job_roles.json")
    load_skills(sim, _DATA_DIR / "skills.json")
    load_species(sim, _DATA_DIR / "species.json")

    default_traits.load_plugin(sim)
    default_character_names.load_plugin(sim)
    default_settlement_names.load_plugin(sim)

    sim.initialize()

    return sim


def test_simulation_step() -> None:
    sim = Simulation()

    assert sim.date.month == 1
    assert sim.date.year == 1
    assert sim.date.total_months == 0

    sim.step()

    assert sim.date.month == 2
    assert sim.date.year == 1
    assert sim.date.total_months == 1

    # advance by many months
    for _ in range(13):
        sim.step()

    assert sim.date.month == 3
    assert sim.date.year == 2
    assert sim.date.total_months == 14


def test_simulation_initialization(test_sim: Simulation) -> None:

    settlements = test_sim.world.get_component(Settlement)

    assert len(settlements) == 1

    assert settlements[0][1].gameobject.metadata["definition_id"] == "basic_settlement"


def test_simulation_to_json(test_sim: Simulation) -> None:

    # Run the simulation for one year (12 months) of simulated time
    for _ in range(12):
        test_sim.step()

    output_file = pathlib.Path(__file__).parent / "output" / "test_output.json"
    output_file.parent.mkdir(exist_ok=True, parents=True)
    with open(output_file, "w", encoding="utf-8") as fp:
        fp.write(test_sim.to_json(2))

    assert True
