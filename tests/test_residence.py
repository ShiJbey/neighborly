import pathlib

from neighborly.components.residence import ResidentialBuilding
from neighborly.helpers.residence import create_residence
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
)
from neighborly.simulation import Simulation

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


def test_create_residence() -> None:
    sim = Simulation()

    load_districts(sim, _DATA_DIR / "districts.json")
    load_settlements(sim, _DATA_DIR / "settlements.json")
    load_businesses(sim, _DATA_DIR / "businesses.json")
    load_characters(sim, _DATA_DIR / "characters.json")
    load_residences(sim, _DATA_DIR / "residences.json")
    load_job_roles(sim, _DATA_DIR / "job_roles.json")

    sim.initialize()

    r0 = create_residence(sim.world, "house")
    r0_units = list(r0.get_component(ResidentialBuilding).units)
    assert len(r0_units) == 1

    r1 = create_residence(sim.world, "large_apartment_building")
    r1_units = list(r1.get_component(ResidentialBuilding).units)
    assert len(r1_units) == 10
