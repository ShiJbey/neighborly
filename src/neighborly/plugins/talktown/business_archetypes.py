from neighborly.core.archetypes import BaseBusinessArchetype
from neighborly.plugins.talktown.business_components import (
    Bakery,
    Bank,
    Bar,
    Barbershop,
    BusDepot,
    CarpentryCompany,
    Cemetery,
    CityHall,
    ClothingStore,
    CoalMine,
    ConstructionFirm,
    Dairy,
    DaycareCenter,
    Deli,
    DentistOffice,
    DepartmentStore,
    Diner,
    Distillery,
    DrugStore,
    Farm,
    FireStation,
    Foundry,
    FurnitureStore,
    GeneralStore,
    GroceryStore,
    HardwareStore,
    Hospital,
    Hotel,
    Inn,
    InsuranceCompany,
    JeweleryShop,
    LawFirm,
    OptometryClinic,
    PaintingCompany,
    Park,
    Pharmacy,
    PlasticSurgeryClinic,
    PlumbingCompany,
    PoliceStation,
    Quarry,
    RealtyFirm,
    Restaurant,
    School,
    ShoemakerShop,
    Supermarket,
    TailorShop,
    TattooParlor,
    Tavern,
    TaxiDepot,
)

bakery = BaseBusinessArchetype(
    business_type=Bakery,
    name_format="Bakery",
    owner_type="Baker",
    employee_types={"Apprentice": 1},
    services=["shopping", "errands"],
)


bank = BaseBusinessArchetype(
    business_type=Bank,
    name_format="Bank",
    hours="day",
    owner_type="Banker",
    services=["errands"],
    employee_types={"Bank Teller": 3, "Janitor": 1, "Manager": 1},
)

bar = BaseBusinessArchetype(
    business_type=Bar,
    name_format="Bar",
    hours="evening",
    owner_type="Owner",
    employee_types={"Bartender": 4, "Manager": 1},
    services=["drinking", "socializing"],
)

barbershop = BaseBusinessArchetype(
    business_type=Barbershop,
    name_format="Barbershop",
    hours="day",
    owner_type="Barber",
    employee_types={"Cashier": 1},
)

bus_depot = BaseBusinessArchetype(
    business_type=BusDepot,
    name_format="Bus Depot",
    hours="day",
    employee_types={
        "Secretary": 1,
        "Bus Driver": 3,
        "Manager": 1,
    },
)

carpentry_company = BaseBusinessArchetype(
    business_type=CarpentryCompany,
    name_format="Carpentry Company",
    owner_type="Carpenter",
    employee_types={"Apprentice": 1, "Builder": 1},
    min_population=70,
    max_instances=1,
)

cemetery = BaseBusinessArchetype(
    business_type=Cemetery,
    name_format="Cemetery",
    owner_type="Mortician",
    employee_types={"Secretary": 1, "Apprentice": 1, "Groundskeeper": 1},
    max_instances=1,
)


city_hall = BaseBusinessArchetype(
    business_type=CityHall,
    name_format="City Hall",
    employee_types={
        "Secretary": 2,
        "Janitor": 1,
    },
    min_population=100,
    max_instances=1,
)

clothing_store = BaseBusinessArchetype(
    business_type=ClothingStore,
    name_format="Clothing Store",
    owner_type="Clothier",
    employee_types={"Cashier": 2, "Seamstress": 1, "Dressmaker": 1, "Tailor": 1},
    max_instances=2,
    services=["shopping"],
)

coal_mine = BaseBusinessArchetype(
    business_type=CoalMine,
    name_format="Coal Mine",
    owner_type="Owner",
    employee_types={"Miner": 2, "Manager": 1},
    max_instances=1,
)

construction_firm = BaseBusinessArchetype(
    business_type=ConstructionFirm,
    name_format="Construction Firm",
    max_instances=1,
    min_population=80,
    owner_type="Architect",
    employee_types={"Secretary": 1, "Builder": 3, "Bricklayer": 1},
)

dairy = BaseBusinessArchetype(
    business_type=Dairy,
    name_format="Dairy",
    owner_type="Milkman",
    employee_types={"Apprentice": 1, "Bottler": 1},
    max_instances=1,
    min_population=30,
)

day_care = BaseBusinessArchetype(
    business_type=DaycareCenter,
    name_format="Daycare Service",
    owner_type="Daycare Provider",
    employee_types={"Daycare Provider": 2},
    min_population=200,
    max_instances=1,
)

deli = BaseBusinessArchetype(
    business_type=Deli,
    name_format="Deli",
    owner_type="Proprietor",
    employee_types={"Cashier": 2, "Manager": 1},
    min_population=100,
    max_instances=2,
    services=["shopping"],
)

dentist_office = BaseBusinessArchetype(
    business_type=DentistOffice,
    name_format="Dentist Office",
    owner_type="Dentist",
    employee_types={"Nurse": 2, "Secretary": 1},
    min_population=75,
)

department_store = BaseBusinessArchetype(
    business_type=DepartmentStore,
    name_format="Department Store",
    owner_type="Owner",
    employee_types={"Cashier": 2, "Manager": 1},
    min_population=200,
    max_instances=1,
    services=["shopping"],
)

diner = BaseBusinessArchetype(
    business_type=Diner,
    name_format="Diner",
    owner_type="Proprietor",
    employee_types={"Cook": 1, "Waiter": 1, "Busboy": 1, "Manager": 1},
    year_available=1945,
    min_population=30,
    max_instances=3,
    services=["food", "socializing"],
)

distillery = BaseBusinessArchetype(
    business_type=Distillery,
    name_format="Distillery",
    owner_type="Distiller",
    employee_types={"Bottler": 1, "Cooper": 1},
    max_instances=1,
)

drug_store = BaseBusinessArchetype(
    business_type=DrugStore,
    name_format="Drug Store",
    owner_type="Druggist",
    employee_types={"Cashier": 1},
    min_population=30,
    max_instances=1,
    services=["shopping"],
)

farm = BaseBusinessArchetype(
    business_type=Farm,
    name_format="Farm",
    owner_type="Farmer",
    employee_types={"Farmhand": 2},
    max_instances=99,
)

fire_station = BaseBusinessArchetype(
    business_type=FireStation,
    name_format="Fire Station",
    employee_types={"Fire Chief": 1, "Fire Fighter": 2},
    min_population=100,
    max_instances=1,
)

foundry = BaseBusinessArchetype(
    business_type=Foundry,
    name_format="Foundry",
    owner_type="Owner",
    employee_types={"Molder": 1, "Puddler": 1},
    year_available=1830,
    year_obsolete=1950,
    min_population=20,
    max_instances=1,
)

furniture_store = BaseBusinessArchetype(
    business_type=FurnitureStore,
    name_format="Furniture Store",
    owner_type="Woodworker",
    employee_types={"Apprentice": 1},
    min_population=20,
    max_instances=1,
    services=["shopping"],
)

general_store = BaseBusinessArchetype(
    business_type=GeneralStore,
    name_format="General Store",
    owner_type="Grocer",
    employee_types={"Manager": 1, "Stocker": 1, "Cashier": 1},
    min_population=20,
    max_instances=2,
    services=["shopping"],
)

grocery_store = BaseBusinessArchetype(
    business_type=GroceryStore,
    name_format="Grocery Store",
    owner_type="Grocer",
    employee_types={"Manager": 1, "Stocker": 1, "Cashier": 1},
    min_population=20,
    max_instances=2,
    services=["shopping"],
)

hardware_store = BaseBusinessArchetype(
    business_type=HardwareStore,
    name_format="Hardware Store",
    owner_type="Proprietor",
    employee_types={"Manager": 1, "Stocker": 1, "Cashier": 1},
    min_population=40,
    max_instances=2,
    services=["shopping"],
)

hospital = BaseBusinessArchetype(
    business_type=Hospital,
    name_format="Hospital",
    employee_types={"Doctor": 2, "Nurse": 1, "Secretary": 1},
    min_population=200,
)

hotel = BaseBusinessArchetype(
    business_type=Hotel,
    name_format="Hotel",
    owner_type="Owner",
    employee_types={"Hotel Maid": 2, "Concierge": 1, "Manager": 1},
)

inn = BaseBusinessArchetype(
    business_type=Inn,
    name_format="Inn",
    owner_type="Innkeeper",
    employee_types={"Hotel Maid": 2, "Concierge": 1, "Manager": 1},
)

insurance_company = BaseBusinessArchetype(
    business_type=InsuranceCompany,
    name_format="Insurance Company",
    owner_type="Insurance Agent",
    employee_types={"Secretary": 1, "Insurance Agent": 2},
    max_instances=1,
)

jewelry_shop = BaseBusinessArchetype(
    business_type=JeweleryShop,
    name_format="Jewelry Shop",
    owner_type="Jeweler",
    employee_types={"Cashier": 1, "Apprentice": 1},
    min_population=200,
    max_instances=1,
    services=["shopping"],
)

law_firm = BaseBusinessArchetype(
    business_type=LawFirm,
    name_format="Law Firm",
    owner_type="Lawyer",
    employee_types={"Lawyer": 1, "Secretary": 1},
    min_population=150,
    max_instances=2,
)


optometry_clinic = BaseBusinessArchetype(
    business_type=OptometryClinic,
    name_format="Optometry Clinic",
    owner_type="Optometrist",
    employee_types={"Secretary": 1, "Nurse": 1},
    year_available=1990,
)

painting_company = BaseBusinessArchetype(
    business_type=PaintingCompany,
    name_format="Painting Company",
    owner_type="Painter",
    employee_types={"Painter": 1, "Plasterer": 1},
)

park = BaseBusinessArchetype(
    business_type=Park,
    name_format="Park",
    employee_types={"Groundskeeper": 1},
    min_population=100,
    max_instances=99,
    services=["shopping", "socializing", "recreation"],
)

pharmacy = BaseBusinessArchetype(
    business_type=Pharmacy,
    name_format="Pharmacy",
    owner_type="Pharmacist",
    employee_types={"Pharmacist": 1, "Cashier": 1},
    year_available=1960,
)

plastic_surgery_clinic = BaseBusinessArchetype(
    business_type=PlasticSurgeryClinic,
    name_format="Plastic Surgery Clinic",
    owner_type="Plastic Surgeon",
    employee_types={"Nurse": 1, "Secretary": 1},
    min_population=200,
    max_instances=1,
    year_available=1970,
)

plumbing_company = BaseBusinessArchetype(
    business_type=PlumbingCompany,
    name_format="Plumbing Company",
    owner_type="Plumber",
    employee_types={"Apprentice": 1, "Secretary": 1},
    min_population=100,
    max_instances=2,
)

police_station = BaseBusinessArchetype(
    business_type=PoliceStation,
    name_format="Police Station",
    employee_types={"Police Chief": 1, "Police Officer": 2},
    min_population=100,
    max_instances=1,
)

quarry = BaseBusinessArchetype(
    business_type=Quarry,
    name_format="Quarry",
    owner_type="Owner",
    employee_types={"Quarryman": 1, "Stone Cutter": 1, "Laborer": 1, "Engineer": 1},
    max_instances=1,
)

realty_firm = BaseBusinessArchetype(
    business_type=RealtyFirm,
    name_format="Realty Firm",
    owner_type="Realtor",
    employee_types={"Realtor": 1, "Secretary": 1},
    min_population=80,
    max_instances=2,
)

restaurant = BaseBusinessArchetype(
    business_type=Restaurant,
    name_format="Restaurant",
    owner_type="Proprietor",
    employee_types={"Waiter": 1, "Cook": 1, "Busboy": 1, "Manager": 1},
    min_population=50,
    services=["food", "socializing"],
)

school = BaseBusinessArchetype(
    business_type=School,
    name_format="School",
    employee_types={"Principal": 1, "Teacher": 2, "Janitor": 1},
    max_instances=1,
)

shoemaker_shop = BaseBusinessArchetype(
    business_type=ShoemakerShop,
    name_format="Shoemaker Shop",
    owner_type="Shoemaker",
    employee_types={"Apprentice": 1},
    services=["shopping"],
)

supermarket = BaseBusinessArchetype(
    business_type=Supermarket,
    name_format="Supermarket",
    owner_type="Owner",
    employee_types={"Cashier": 1, "Stocker": 1, "Manager": 1},
    min_population=200,
    max_instances=1,
    services=["shopping"],
)

tailor_shop = BaseBusinessArchetype(
    business_type=TailorShop,
    name_format="Tailor Shop",
    owner_type="Tailor",
    employee_types={"Apprentice": 1},
    min_population=40,
    max_instances=1,
    services=["shopping"],
)

tattoo_parlor = BaseBusinessArchetype(
    business_type=TattooParlor,
    name_format="Tattoo Parlor",
    year_available=1970,
    min_population=300,
    max_instances=1,
    owner_type="Tattoo Artist",
    employee_types={"Cashier": 1},
    hours="afternoon",
)

tavern = BaseBusinessArchetype(
    business_type=Tavern,
    name_format="Tavern",
    hours="evening",
    employee_types={"Cook": 1, "Bartender": 1, "Waiter": 1},
    min_population=20,
    services=["drinking", "socializing"],
)


taxi_depot = BaseBusinessArchetype(
    business_type=TaxiDepot,
    name_format="Taxi Depot",
    owner_type="Proprietor",
    employee_types={"Taxi Driver": 3},
    max_instances=1,
    year_available=1930,
    year_obsolete=9999,
    hours="day",
)
