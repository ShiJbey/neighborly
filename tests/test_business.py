import pathlib

from neighborly.components.business import Business
from neighborly.defs.base_types import (
    BusinessGenOptions,
    DistrictGenOptions,
    SettlementGenOptions,
)
from neighborly.helpers.business import create_business
from neighborly.helpers.settlement import create_district, create_settlement
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

    settlement = create_settlement(
        sim.world, SettlementGenOptions(definition_id="basic_settlement")
    )

    district = create_district(
        sim.world,
        settlement,
        DistrictGenOptions(definition_id="entertainment_district"),
    )

    business = create_business(
        sim.world, district, BusinessGenOptions(definition_id="blacksmith_shop")
    )

    assert business.get_component(Business).owner_role is not None
    assert business.get_component(Business).district == district
