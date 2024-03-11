"""Tests for data loaders.

"""

import pathlib

from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    JobRoleLibrary,
    ResidenceLibrary,
    SettlementLibrary,
    SkillLibrary,
    TraitLibrary,
)
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
    load_skills,
    load_tracery,
    load_traits,
)
from neighborly.simulation import Simulation
from neighborly.tracery import Tracery

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def test_load_residences() -> None:
    sim = Simulation()
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    library = sim.world.resources.get_resource(ResidenceLibrary)

    residence_def = library.get_definition("house")

    assert residence_def.definition_id == "house"


def test_load_settlements() -> None:
    sim = Simulation()
    load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    library = sim.world.resources.get_resource(SettlementLibrary)

    settlement_def = library.get_definition("basic_settlement")

    assert settlement_def.definition_id == "basic_settlement"


def test_load_business() -> None:
    sim = Simulation()
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    library = sim.world.resources.get_resource(BusinessLibrary)

    business_def = library.get_definition("cafe")

    assert business_def.definition_id == "cafe"


def test_load_characters() -> None:
    sim = Simulation()
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    library = sim.world.resources.get_resource(CharacterLibrary)

    character_def = library.get_definition("person")

    assert character_def.definition_id == "person"


def test_load_districts() -> None:
    sim = Simulation()
    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    library = sim.world.resources.get_resource(DistrictLibrary)

    district_def = library.get_definition("market_district")

    assert district_def.definition_id == "market_district"


def test_load_traits() -> None:
    sim = Simulation()
    load_traits(sim, _TEST_DATA_DIR / "traits.json")
    library = sim.world.resources.get_resource(TraitLibrary)

    trait_def = library.get_definition("flirtatious")

    assert trait_def.definition_id == "flirtatious"


def test_load_job_roles() -> None:
    sim = Simulation()
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")
    library = sim.world.resources.get_resource(JobRoleLibrary)

    trait_def = library.get_definition("blacksmith")

    assert trait_def.definition_id == "blacksmith"


def test_load_names() -> None:
    sim = Simulation()

    load_tracery(sim, _TEST_DATA_DIR / "sample.tracery.json")

    tracery = sim.world.resources.get_resource(Tracery)

    generated_name = tracery.generate("#simpsons_name#")

    assert generated_name in {"Homer", "Marge", "Maggie", "Lisa", "Bart"}


def test_load_skills() -> None:
    """Test loading skill definitions from a data file."""

    sim = Simulation()
    load_skills(sim, _TEST_DATA_DIR / "skills.json")
    library = sim.world.resources.get_resource(SkillLibrary)

    definition = library.get_definition("blacksmithing")

    assert definition.definition_id == "blacksmithing"
