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
    sim = Simulation(SimulationConfig(settlement_with_id="basic_settlement"))

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
