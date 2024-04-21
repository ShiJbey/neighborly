import pathlib

from neighborly.components.business import Business
from neighborly.helpers.business import create_business
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


def test_create_business() -> None:
    sim = Simulation()

    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")

    sim.initialize()

    business = create_business(sim.world, "blacksmith_shop")

    assert business.get_component(Business).owner_role is not None
