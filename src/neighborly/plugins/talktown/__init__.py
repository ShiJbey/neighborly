import pathlib
from typing import Any, Dict, List

import pandas as pd

from neighborly.loaders import load_occupation_types, load_prefabs
from neighborly.plugins.talktown import business_components
from neighborly.plugins.talktown.personality import (
    BigFivePersonality,
    BigFivePersonalityFactory,
)
from neighborly.plugins.talktown.school import (
    CollegeGraduate,
    EnrollInSchoolSystem,
    GraduateAdultStudentsSystem,
    SchoolSystemGroup,
    Student,
)
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.systems import EarlyUpdateSystemGroup

plugin_info = PluginInfo(
    name="Talk of the Town Plugin",
    plugin_id="default.talktown",
    version="0.1.0",
)


def _load_business_spawn_table_info(sim: Neighborly, filepath: pathlib.Path) -> None:
    """Loads business spawn table entries from a *.csv file."""
    entries: List[Dict[str, Any]] = []

    df: pd.DataFrame = pd.read_csv(filepath)  # type: ignore

    for _, row in df.iterrows():  # type: ignore
        entries.append({**row})

    # Add this to the simulation config
    business_spawn_table = sim.config.settings.get("business_spawn_table", [])
    business_spawn_table.extend(entries)
    sim.config.settings["business_spawn_table"] = business_spawn_table


def setup(sim: Neighborly, **kwargs: Any) -> None:
    sim.world.system_manager.add_system(
        SchoolSystemGroup(), system_group=EarlyUpdateSystemGroup
    )
    sim.world.system_manager.add_system(
        EnrollInSchoolSystem(), system_group=SchoolSystemGroup
    )
    sim.world.system_manager.add_system(
        GraduateAdultStudentsSystem(), system_group=SchoolSystemGroup
    )

    # Register student component for school system
    sim.world.gameobject_manager.register_component(Student)
    sim.world.gameobject_manager.register_component(CollegeGraduate)

    # Register Personality component
    sim.world.gameobject_manager.register_component(
        BigFivePersonality, factory=BigFivePersonalityFactory()
    )

    # Register Business components
    sim.world.gameobject_manager.register_component(
        business_components.ApartmentComplex
    )
    sim.world.gameobject_manager.register_component(business_components.Bakery)
    sim.world.gameobject_manager.register_component(business_components.Bank)
    sim.world.gameobject_manager.register_component(business_components.Bar)
    sim.world.gameobject_manager.register_component(business_components.BarberShop)
    sim.world.gameobject_manager.register_component(business_components.BlacksmithShop)
    sim.world.gameobject_manager.register_component(business_components.Brewery)
    sim.world.gameobject_manager.register_component(business_components.BusDepot)
    sim.world.gameobject_manager.register_component(business_components.ButcherShop)
    sim.world.gameobject_manager.register_component(business_components.CandyStore)
    sim.world.gameobject_manager.register_component(
        business_components.CarpentryCompany
    )
    sim.world.gameobject_manager.register_component(business_components.Cemetery)
    sim.world.gameobject_manager.register_component(business_components.CityHall)
    sim.world.gameobject_manager.register_component(business_components.ClothingStore)
    sim.world.gameobject_manager.register_component(business_components.CoalMine)
    sim.world.gameobject_manager.register_component(
        business_components.ConstructionFirm
    )
    sim.world.gameobject_manager.register_component(business_components.Dairy)
    sim.world.gameobject_manager.register_component(business_components.DaycareCenter)
    sim.world.gameobject_manager.register_component(business_components.Deli)
    sim.world.gameobject_manager.register_component(business_components.DentistOffice)
    sim.world.gameobject_manager.register_component(business_components.DepartmentStore)
    sim.world.gameobject_manager.register_component(business_components.Diner)
    sim.world.gameobject_manager.register_component(business_components.Distillery)
    sim.world.gameobject_manager.register_component(business_components.DrugStore)
    sim.world.gameobject_manager.register_component(business_components.Farm)
    sim.world.gameobject_manager.register_component(business_components.FireStation)
    sim.world.gameobject_manager.register_component(business_components.Foundry)
    sim.world.gameobject_manager.register_component(business_components.FurnitureStore)
    sim.world.gameobject_manager.register_component(business_components.GeneralStore)
    sim.world.gameobject_manager.register_component(business_components.GroceryStore)
    sim.world.gameobject_manager.register_component(business_components.HardwareStore)
    sim.world.gameobject_manager.register_component(business_components.Hospital)
    sim.world.gameobject_manager.register_component(business_components.Hotel)
    sim.world.gameobject_manager.register_component(business_components.Inn)
    sim.world.gameobject_manager.register_component(
        business_components.InsuranceCompany
    )
    sim.world.gameobject_manager.register_component(business_components.JewelryShop)
    sim.world.gameobject_manager.register_component(business_components.LawFirm)
    sim.world.gameobject_manager.register_component(business_components.OptometryClinic)
    sim.world.gameobject_manager.register_component(business_components.PaintingCompany)
    sim.world.gameobject_manager.register_component(business_components.Park)
    sim.world.gameobject_manager.register_component(business_components.Pharmacy)
    sim.world.gameobject_manager.register_component(
        business_components.PlasticSurgeryClinic
    )
    sim.world.gameobject_manager.register_component(business_components.PlumbingCompany)
    sim.world.gameobject_manager.register_component(business_components.PoliceStation)
    sim.world.gameobject_manager.register_component(business_components.Quarry)
    sim.world.gameobject_manager.register_component(business_components.RealtyFirm)
    sim.world.gameobject_manager.register_component(business_components.Restaurant)
    sim.world.gameobject_manager.register_component(business_components.School)
    sim.world.gameobject_manager.register_component(business_components.ShoemakerShop)
    sim.world.gameobject_manager.register_component(business_components.Supermarket)
    sim.world.gameobject_manager.register_component(business_components.TailorShop)
    sim.world.gameobject_manager.register_component(business_components.TattooParlor)
    sim.world.gameobject_manager.register_component(business_components.Tavern)
    sim.world.gameobject_manager.register_component(business_components.TaxiDepot)
    sim.world.gameobject_manager.register_component(business_components.University)

    # Load remaining data from data files
    load_occupation_types(sim.world, pathlib.Path(__file__).parent / "occupations.yaml")
    load_prefabs(sim.world, pathlib.Path(__file__).parent / "businesses.yaml")
    _load_business_spawn_table_info(
        sim, pathlib.Path(__file__).parent / "business_spawn_table.csv"
    )
