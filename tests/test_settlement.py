import pathlib

from neighborly.components.settlement import Settlement
from neighborly.helpers.settlement import create_settlement
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
)
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def test_create_settlement() -> None:
    sim = Simulation()

    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")

    settlement = create_settlement(sim.world, "basic_settlement")

    assert settlement.metadata["definition_id"] == "basic_settlement"

    districts = list(settlement.get_component(Settlement).districts)

    assert len(districts) == 4
