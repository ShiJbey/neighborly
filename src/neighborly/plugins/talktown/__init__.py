import pathlib
from typing import Any, Dict, List

import pandas as pd

from neighborly.components.business import register_occupation_type
from neighborly.loaders import load_prefabs
from neighborly.plugins.talktown import business_components, occupations
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


def setup(sim: Neighborly):
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

    # Occupation types
    register_occupation_type(sim.world, occupations.Apprentice)
    register_occupation_type(sim.world, occupations.Architect)
    register_occupation_type(sim.world, occupations.Bottler)
    register_occupation_type(sim.world, occupations.Bricklayer)
    register_occupation_type(sim.world, occupations.Builder)
    register_occupation_type(sim.world, occupations.Cashier)
    register_occupation_type(sim.world, occupations.Cook)
    register_occupation_type(sim.world, occupations.Dishwasher)
    register_occupation_type(sim.world, occupations.Groundskeeper)
    register_occupation_type(sim.world, occupations.HotelMaid)
    register_occupation_type(sim.world, occupations.Janitor)
    register_occupation_type(sim.world, occupations.Laborer)
    register_occupation_type(sim.world, occupations.Secretary)
    register_occupation_type(sim.world, occupations.Waiter)
    register_occupation_type(sim.world, occupations.WhiteWasher)
    register_occupation_type(sim.world, occupations.Busboy)
    register_occupation_type(sim.world, occupations.Stocker)
    register_occupation_type(sim.world, occupations.Seamstress)
    register_occupation_type(sim.world, occupations.Farmer)
    register_occupation_type(sim.world, occupations.Farmhand)
    register_occupation_type(sim.world, occupations.Miner)
    register_occupation_type(sim.world, occupations.Painter)
    register_occupation_type(sim.world, occupations.Banker)
    register_occupation_type(sim.world, occupations.BankTeller)
    register_occupation_type(sim.world, occupations.Grocer)
    register_occupation_type(sim.world, occupations.Bartender)
    register_occupation_type(sim.world, occupations.Concierge)
    register_occupation_type(sim.world, occupations.DaycareProvider)
    register_occupation_type(sim.world, occupations.Landlord)
    register_occupation_type(sim.world, occupations.Baker)
    register_occupation_type(sim.world, occupations.Cooper)
    register_occupation_type(sim.world, occupations.Barkeeper)
    register_occupation_type(sim.world, occupations.Milkman)
    register_occupation_type(sim.world, occupations.Plasterer)
    register_occupation_type(sim.world, occupations.Barber)
    register_occupation_type(sim.world, occupations.Butcher)
    register_occupation_type(sim.world, occupations.FireFighter)
    register_occupation_type(sim.world, occupations.Carpenter)
    register_occupation_type(sim.world, occupations.TaxiDriver)
    register_occupation_type(sim.world, occupations.BusDriver)
    register_occupation_type(sim.world, occupations.Blacksmith)
    register_occupation_type(sim.world, occupations.Woodworker)
    register_occupation_type(sim.world, occupations.StoneCutter)
    register_occupation_type(sim.world, occupations.Dressmaker)
    register_occupation_type(sim.world, occupations.Distiller)
    register_occupation_type(sim.world, occupations.Plumber)
    register_occupation_type(sim.world, occupations.Joiner)
    register_occupation_type(sim.world, occupations.Innkeeper)
    register_occupation_type(sim.world, occupations.Nurse)
    register_occupation_type(sim.world, occupations.Shoemaker)
    register_occupation_type(sim.world, occupations.Brewer)
    register_occupation_type(sim.world, occupations.TattooArtist)
    register_occupation_type(sim.world, occupations.Puddler)
    register_occupation_type(sim.world, occupations.Clothier)
    register_occupation_type(sim.world, occupations.Teacher)
    register_occupation_type(sim.world, occupations.Principal)
    register_occupation_type(sim.world, occupations.Tailor)
    register_occupation_type(sim.world, occupations.Molder)
    register_occupation_type(sim.world, occupations.Turner)
    register_occupation_type(sim.world, occupations.QuarryMan)
    register_occupation_type(sim.world, occupations.Proprietor)
    register_occupation_type(sim.world, occupations.Dentist)
    register_occupation_type(sim.world, occupations.Doctor)
    register_occupation_type(sim.world, occupations.Druggist)
    register_occupation_type(sim.world, occupations.Engineer)
    register_occupation_type(sim.world, occupations.FireChief)
    register_occupation_type(sim.world, occupations.InsuranceAgent)
    register_occupation_type(sim.world, occupations.Jeweler)
    register_occupation_type(sim.world, occupations.Lawyer)
    register_occupation_type(sim.world, occupations.Manager)
    register_occupation_type(sim.world, occupations.Mayor)
    register_occupation_type(sim.world, occupations.Mortician)
    register_occupation_type(sim.world, occupations.Owner)
    register_occupation_type(sim.world, occupations.Professor)
    register_occupation_type(sim.world, occupations.Optometrist)
    register_occupation_type(sim.world, occupations.Pharmacist)
    register_occupation_type(sim.world, occupations.PlasticSurgeon)
    register_occupation_type(sim.world, occupations.PoliceChief)
    register_occupation_type(sim.world, occupations.PoliceOfficer)
    register_occupation_type(sim.world, occupations.Realtor)

    # Load remaining data from data files
    load_prefabs(sim.world, pathlib.Path(__file__).parent / "businesses.yaml")
    _load_business_spawn_table_info(
        sim, pathlib.Path(__file__).parent / "business_spawn_table.csv"
    )
