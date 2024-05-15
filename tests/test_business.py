"""Test business-related functionality.

"""

import pathlib

from neighborly.components.business import Business
from neighborly.helpers.business import create_business
from neighborly.loaders import load_businesses, load_job_roles
from neighborly.simulation import Simulation

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


def test_create_business() -> None:
    """Test business creation using create_business."""

    sim = Simulation()

    load_businesses(sim, _DATA_DIR / "businesses.json")
    load_job_roles(sim, _DATA_DIR / "job_roles.json")

    sim.initialize()

    business = create_business(sim.world, "blacksmith_shop")

    assert business.get_component(Business).owner_role is not None
