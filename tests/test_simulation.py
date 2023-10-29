import pathlib

from neighborly.components.settlement import Settlement
from neighborly.config import SimulationConfig
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
    load_skills,
)
from neighborly.plugins import (
    default_character_names,
    default_settlement_names,
    default_traits,
)
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


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


def test_simulation_initialization() -> None:
    sim = Simulation(SimulationConfig(settlement="basic_settlement"))

    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    # Settlements are created at the beginning of the first time step
    sim.initialize()

    settlements = sim.world.get_component(Settlement)

    assert len(settlements) == 1

    assert settlements[0][1].gameobject.metadata["definition_id"] == "basic_settlement"


def test_simulation_to_json() -> None:
    sim = Simulation(SimulationConfig(settlement="basic_settlement"))

    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)
    default_character_names.load_plugin(sim)
    default_settlement_names.load_plugin(sim)

    # Run the simulation for one year (12 months) of simulated time
    for _ in range(12):
        sim.step()

    output_file = pathlib.Path(__file__).parent / "output" / "test_output.json"
    output_file.parent.mkdir(exist_ok=True, parents=True)
    with open(output_file, "w", encoding="utf-8") as fp:
        fp.write(sim.to_json(2))

    assert True
