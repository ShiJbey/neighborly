import pathlib

from neighborly.components.settlement import Settlement
from neighborly.defs.base_types import SettlementDefDistrictEntry
from neighborly.defs.defaults import DefaultSettlementDef
from neighborly.helpers.settlement import create_settlement
from neighborly.libraries import DistrictLibrary, SettlementLibrary
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


def test_required_tags() -> None:

    sim = Simulation()

    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    # load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")

    sim.world.resource_manager.get_resource(SettlementLibrary).add_definition(
        DefaultSettlementDef(
            definition_id = "basic_settlement",
            display_name="Settlement",
            districts = [
                SettlementDefDistrictEntry(
                    tags=["urban", "suburban"]
                ),
                SettlementDefDistrictEntry(
                    tags=["urban", "suburban"]
                )
            ]
        )
    )

    #it doesn't actually check if the tags match, just if the amount matches

    # sim.world.resource_manager.get_resource(SettlementLibrary).add_definition(
    #     DefaultSettlementDef(
    #         definition_id = "basic_settlement2",
    #         display_name="Settlement",
    #         districts = [
    #             SettlementDefDistrictEntry(
    #                 tags=["commercial", "suburban"]
    #             ),

    #         ]
    #     )
    # )

    settlement = create_settlement(sim.world, "basic_settlement")
    library = settlement.world.resource_manager.get_resource(DistrictLibrary)



    required_tags = ["suburban", "urban"]
    districts = list(settlement.get_component(Settlement).districts)

    for district in districts:
        district_def = library.get_definition(district.metadata["definition_id"])
        assert all(tag in district_def.tags for tag in required_tags), "Missing tags"

    #assert False

#Both have the same issue
def test_optional_tags() -> None:

    sim = Simulation()

    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    # load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")

    sim.world.resource_manager.get_resource(SettlementLibrary).add_definition(
        DefaultSettlementDef(
            definition_id = "basic_settlement",
            display_name="Settlement",
            districts = [
                SettlementDefDistrictEntry(
                    tags=["urban", "suburban", "~hot", "~heat"]
                ),
                SettlementDefDistrictEntry(
                    tags=["urban", "suburban", "~hot", "~heat"]
                )

            ]
        )
    )

    #it doesn't actually check if the tags match, just if the amount matches

    # sim.world.resource_manager.get_resource(SettlementLibrary).add_definition(
    #     DefaultSettlementDef(
    #         definition_id = "basic_settlement2",
    #         display_name="Settlement",
    #         districts = [
    #             SettlementDefDistrictEntry(
    #                 tags=["commercial", "suburban"]
    #             ),

    #         ]
    #     )
    # )

    settlement = create_settlement(sim.world, "basic_settlement")
    library = settlement.world.resource_manager.get_resource(DistrictLibrary)



    required_tags = ["suburban", "urban"]
    districts = list(settlement.get_component(Settlement).districts)

    for district in districts:
        district_def = library.get_definition(district.metadata["definition_id"])
        assert all(tag in district_def.tags for tag in required_tags), "Missing tags"