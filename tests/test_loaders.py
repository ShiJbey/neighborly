"""Tests for data loaders.

"""

import pathlib

from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    JobRoleLibrary,
    SettlementLibrary,
    SkillLibrary,
    TraitLibrary,
)
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_settlements,
    load_skills,
    load_traits,
)
from neighborly.simulation import Simulation

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


def test_load_settlements() -> None:
    sim = Simulation()
    load_settlements(sim, _DATA_DIR / "settlements.json")
    library = sim.world.resource_manager.get_resource(SettlementLibrary)

    settlement_def = library.get_definition("basic_settlement")

    assert settlement_def.definition_id == "basic_settlement"


def test_load_business() -> None:
    sim = Simulation()
    load_businesses(sim, _DATA_DIR / "businesses.json")
    library = sim.world.resource_manager.get_resource(BusinessLibrary)

    business_def = library.get_definition("cafe")

    assert business_def.definition_id == "cafe"


def test_load_characters() -> None:
    sim = Simulation()
    load_characters(sim, _DATA_DIR / "characters.json")
    library = sim.world.resource_manager.get_resource(CharacterLibrary)

    character_def = library.get_definition("base_character")

    assert character_def.definition_id == "base_character"


def test_load_districts() -> None:
    sim = Simulation()
    load_districts(sim, _DATA_DIR / "districts.json")
    library = sim.world.resource_manager.get_resource(DistrictLibrary)

    district_def = library.get_definition("market_district")

    assert district_def.definition_id == "market_district"


def test_load_traits() -> None:
    sim = Simulation()
    load_traits(sim, _DATA_DIR / "traits.json")
    library = sim.world.resource_manager.get_resource(TraitLibrary)

    trait_def = library.get_definition("flirtatious")

    assert trait_def.definition_id == "flirtatious"


def test_load_job_roles() -> None:
    sim = Simulation()
    load_job_roles(sim, _DATA_DIR / "job_roles.json")
    library = sim.world.resource_manager.get_resource(JobRoleLibrary)

    trait_def = library.get_definition("blacksmith")

    assert trait_def.definition_id == "blacksmith"


def test_load_skills() -> None:
    """Test loading skill definitions from a data file."""

    sim = Simulation()
    load_skills(sim, _DATA_DIR / "skills.json")
    library = sim.world.resource_manager.get_resource(SkillLibrary)

    definition = library.get_definition("blacksmithing")

    assert definition.definition_id == "blacksmithing"
