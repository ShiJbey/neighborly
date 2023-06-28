import pathlib
from typing import Any

from neighborly.loaders import (
    load_activities,
    load_occupation_types,
    load_prefabs,
    load_services,
)
from neighborly.plugins.talktown import business_components
from neighborly.plugins.talktown.personality import (
    BigFivePersonality,
    BigFivePersonalityFactory,
)
from neighborly.plugins.talktown.school import CollegeGraduate, SchoolSystem, Student
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="Talk of the Town",
    plugin_id="default.talktown",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any) -> None:
    sim.world.add_system(SchoolSystem())

    # Register student component for school system
    sim.world.register_component(Student)
    sim.world.register_component(CollegeGraduate)

    # Register Personality component
    sim.world.register_component(
        BigFivePersonality, factory=BigFivePersonalityFactory()
    )

    # Load Services and Activities
    load_services(sim.world, pathlib.Path(__file__).parent / "services.yaml")
    load_activities(sim.world, pathlib.Path(__file__).parent / "activities.yaml")

    # Register Business components
    sim.world.register_component(business_components.ApartmentComplex)
    sim.world.register_component(business_components.Bakery)
    sim.world.register_component(business_components.Bank)
    sim.world.register_component(business_components.Bar)
    sim.world.register_component(business_components.BarberShop)
    sim.world.register_component(business_components.BlacksmithShop)
    sim.world.register_component(business_components.Brewery)
    sim.world.register_component(business_components.BusDepot)
    sim.world.register_component(business_components.ButcherShop)
    sim.world.register_component(business_components.CandyStore)
    sim.world.register_component(business_components.CarpentryCompany)
    sim.world.register_component(business_components.Cemetery)
    sim.world.register_component(business_components.CityHall)
    sim.world.register_component(business_components.ClothingStore)
    sim.world.register_component(business_components.CoalMine)
    sim.world.register_component(business_components.ConstructionFirm)
    sim.world.register_component(business_components.Dairy)
    sim.world.register_component(business_components.DaycareCenter)
    sim.world.register_component(business_components.Deli)
    sim.world.register_component(business_components.DentistOffice)
    sim.world.register_component(business_components.DepartmentStore)
    sim.world.register_component(business_components.Diner)
    sim.world.register_component(business_components.Distillery)
    sim.world.register_component(business_components.DrugStore)
    sim.world.register_component(business_components.Farm)
    sim.world.register_component(business_components.FireStation)
    sim.world.register_component(business_components.Foundry)
    sim.world.register_component(business_components.FurnitureStore)
    sim.world.register_component(business_components.GeneralStore)
    sim.world.register_component(business_components.GroceryStore)
    sim.world.register_component(business_components.HardwareStore)
    sim.world.register_component(business_components.Hospital)
    sim.world.register_component(business_components.Hotel)
    sim.world.register_component(business_components.Inn)
    sim.world.register_component(business_components.InsuranceCompany)
    sim.world.register_component(business_components.JewelryShop)
    sim.world.register_component(business_components.LawFirm)
    sim.world.register_component(business_components.OptometryClinic)
    sim.world.register_component(business_components.PaintingCompany)
    sim.world.register_component(business_components.Park)
    sim.world.register_component(business_components.Pharmacy)
    sim.world.register_component(business_components.PlasticSurgeryClinic)
    sim.world.register_component(business_components.PlumbingCompany)
    sim.world.register_component(business_components.PoliceStation)
    sim.world.register_component(business_components.Quarry)
    sim.world.register_component(business_components.RealtyFirm)
    sim.world.register_component(business_components.Restaurant)
    sim.world.register_component(business_components.School)
    sim.world.register_component(business_components.ShoemakerShop)
    sim.world.register_component(business_components.Supermarket)
    sim.world.register_component(business_components.TailorShop)
    sim.world.register_component(business_components.TattooParlor)
    sim.world.register_component(business_components.Tavern)
    sim.world.register_component(business_components.TaxiDepot)
    sim.world.register_component(business_components.University)

    # Load remaining data from data files
    load_occupation_types(sim.world, pathlib.Path(__file__).parent / "occupations.yaml")
    load_prefabs(sim.world, pathlib.Path(__file__).parent / "businesses.yaml")
