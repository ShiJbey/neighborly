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
    sim.world.gameobject_manager.register_component(occupations.Apprentice)
    sim.world.gameobject_manager.register_component(occupations.Architect)
    sim.world.gameobject_manager.register_component(occupations.Bottler)
    sim.world.gameobject_manager.register_component(occupations.Bricklayer)
    sim.world.gameobject_manager.register_component(occupations.Builder)
    sim.world.gameobject_manager.register_component(occupations.Cashier)
    sim.world.gameobject_manager.register_component(occupations.Cook)
    sim.world.gameobject_manager.register_component(occupations.Dishwasher)
    sim.world.gameobject_manager.register_component(occupations.Groundskeeper)
    sim.world.gameobject_manager.register_component(occupations.HotelMaid)
    sim.world.gameobject_manager.register_component(occupations.Janitor)
    sim.world.gameobject_manager.register_component(occupations.Laborer)
    sim.world.gameobject_manager.register_component(occupations.Secretary)
    sim.world.gameobject_manager.register_component(occupations.Waiter)
    sim.world.gameobject_manager.register_component(occupations.WhiteWasher)
    sim.world.gameobject_manager.register_component(occupations.Busboy)
    sim.world.gameobject_manager.register_component(occupations.Stocker)
    sim.world.gameobject_manager.register_component(occupations.Seamstress)
    sim.world.gameobject_manager.register_component(occupations.Farmer)
    sim.world.gameobject_manager.register_component(occupations.Farmhand)
    sim.world.gameobject_manager.register_component(occupations.Miner)
    sim.world.gameobject_manager.register_component(occupations.Painter)
    sim.world.gameobject_manager.register_component(occupations.Banker)
    sim.world.gameobject_manager.register_component(occupations.BankTeller)
    sim.world.gameobject_manager.register_component(occupations.Grocer)
    sim.world.gameobject_manager.register_component(occupations.Bartender)
    sim.world.gameobject_manager.register_component(occupations.Concierge)
    sim.world.gameobject_manager.register_component(occupations.DaycareProvider)
    sim.world.gameobject_manager.register_component(occupations.Landlord)
    sim.world.gameobject_manager.register_component(occupations.Baker)
    sim.world.gameobject_manager.register_component(occupations.Cooper)
    sim.world.gameobject_manager.register_component(occupations.Barkeeper)
    sim.world.gameobject_manager.register_component(occupations.Milkman)
    sim.world.gameobject_manager.register_component(occupations.Plasterer)
    sim.world.gameobject_manager.register_component(occupations.Barber)
    sim.world.gameobject_manager.register_component(occupations.Butcher)
    sim.world.gameobject_manager.register_component(occupations.FireFighter)
    sim.world.gameobject_manager.register_component(occupations.Carpenter)
    sim.world.gameobject_manager.register_component(occupations.TaxiDriver)
    sim.world.gameobject_manager.register_component(occupations.BusDriver)
    sim.world.gameobject_manager.register_component(occupations.Blacksmith)
    sim.world.gameobject_manager.register_component(occupations.Woodworker)
    sim.world.gameobject_manager.register_component(occupations.StoneCutter)
    sim.world.gameobject_manager.register_component(occupations.Dressmaker)
    sim.world.gameobject_manager.register_component(occupations.Distiller)
    sim.world.gameobject_manager.register_component(occupations.Plumber)
    sim.world.gameobject_manager.register_component(occupations.Joiner)
    sim.world.gameobject_manager.register_component(occupations.Innkeeper)
    sim.world.gameobject_manager.register_component(occupations.Nurse)
    sim.world.gameobject_manager.register_component(occupations.Shoemaker)
    sim.world.gameobject_manager.register_component(occupations.Brewer)
    sim.world.gameobject_manager.register_component(occupations.TattooArtist)
    sim.world.gameobject_manager.register_component(occupations.Puddler)
    sim.world.gameobject_manager.register_component(occupations.Clothier)
    sim.world.gameobject_manager.register_component(occupations.Teacher)
    sim.world.gameobject_manager.register_component(occupations.Principal)
    sim.world.gameobject_manager.register_component(occupations.Tailor)
    sim.world.gameobject_manager.register_component(occupations.Molder)
    sim.world.gameobject_manager.register_component(occupations.Turner)
    sim.world.gameobject_manager.register_component(occupations.QuarryMan)
    sim.world.gameobject_manager.register_component(occupations.Proprietor)
    sim.world.gameobject_manager.register_component(occupations.Dentist)
    sim.world.gameobject_manager.register_component(occupations.Doctor)
    sim.world.gameobject_manager.register_component(occupations.Druggist)
    sim.world.gameobject_manager.register_component(occupations.Engineer)
    sim.world.gameobject_manager.register_component(occupations.FireChief)
    sim.world.gameobject_manager.register_component(occupations.InsuranceAgent)
    sim.world.gameobject_manager.register_component(occupations.Jeweler)
    sim.world.gameobject_manager.register_component(occupations.Lawyer)
    sim.world.gameobject_manager.register_component(occupations.Manager)
    sim.world.gameobject_manager.register_component(occupations.Mayor)
    sim.world.gameobject_manager.register_component(occupations.Mortician)
    sim.world.gameobject_manager.register_component(occupations.Owner)
    sim.world.gameobject_manager.register_component(occupations.Professor)
    sim.world.gameobject_manager.register_component(occupations.Optometrist)
    sim.world.gameobject_manager.register_component(occupations.Pharmacist)
    sim.world.gameobject_manager.register_component(occupations.PlasticSurgeon)
    sim.world.gameobject_manager.register_component(occupations.PoliceChief)
    sim.world.gameobject_manager.register_component(occupations.PoliceOfficer)
    sim.world.gameobject_manager.register_component(occupations.Realtor)
