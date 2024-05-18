import pathlib

from neighborly.helpers.settlement import create_settlement
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_settlements,
)
from neighborly.plugins import default_settlement_names
from neighborly.simulation import Simulation

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


def test_create_settlement() -> None:
    sim = Simulation()

    load_districts(sim, _DATA_DIR / "districts.json")
    load_settlements(sim, _DATA_DIR / "settlements.json")
    load_businesses(sim, _DATA_DIR / "businesses.json")
    load_characters(sim, _DATA_DIR / "characters.json")
    load_job_roles(sim, _DATA_DIR / "job_roles.json")

    default_settlement_names.load_plugin(sim)

    sim.initialize()

    settlement = create_settlement(sim.world, "basic_settlement")

    assert settlement.metadata["definition_id"] == "basic_settlement"
