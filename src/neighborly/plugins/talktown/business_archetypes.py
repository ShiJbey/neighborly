from neighborly.core.business import BusinessArchetype

apartment_complex = BusinessArchetype(
    name="Apartment Complex",
    hours=["day"],
    owner_type="Landlord",
    max_instances=99,
    min_population=50,
    services=["housing"],
    # TODO: Create and add component for ApartmentComplexes
    extra_components={},
    employee_types={
        "Janitor": 1,
    },
)


bakery = BusinessArchetype(
    name="Bakery",
    owner_type="Baker",
    employee_types={"Apprentice": 1},
    services=["shopping", "errands"],
)

bank = BusinessArchetype(
    name="Bank",
    hours=["day", "afternoon"],
    owner_type="Banker",
    services=["errands"],
    employee_types={"Bank Teller": 3, "Janitor": 1, "Manager": 1},
)

bar = BusinessArchetype(
    name="Bar",
    hours=["evening", "night"],
    owner_type="Owner",
    employee_types={"Bartender": 4, "Manager": 1},
    services=["drinking", "socializing"],
)

barbershop = BusinessArchetype(
    name="Barbershop", hours=["day"], owner_type="Barber", employee_types={"Cashier": 1}
)

bus_depot = BusinessArchetype(
    name="Bus Depot",
    hours=["day", "evening"],
    employee_types={
        "Secretary": 1,
        "Bus Driver": 3,
        "Manager": 1,
    },
)

carpentry_company = BusinessArchetype(
    name="Carpentry Company",
    owner_type="Carpenter",
    employee_types={"Apprentice": 1, "Builder": 1},
    min_population=70,
    max_instances=1,
)

cemetery = BusinessArchetype(
    name="Cemetery",
    owner_type="Mortician",
    employee_types={"Secretary": 1, "Apprentice": 1, "Groundskeeper": 1},
    max_instances=1,
)


city_hall = BusinessArchetype(
    name="City Hall",
    employee_types={
        "Secretary": 2,
        "Janitor": 1,
    },
    min_population=100,
    max_instances=1,
)

clothing_store = BusinessArchetype(
    name="Clothing Store",
    owner_type="Clothier",
    employee_types={"Cashier": 2, "Seamstress": 1, "Dressmaker": 1, "Tailor": 1},
    max_instances=2,
    services=["shopping"],
)

coal_mine = BusinessArchetype(
    name="Coal Mine",
    owner_type="Owner",
    employee_types={"Miner": 2, "Manager": 1},
    max_instances=1,
)

construction_firm = BusinessArchetype(
    name="Construction Firm",
    max_instances=1,
    min_population=80,
    owner_type="Architect",
    employee_types={"Secretary": 1, "Builder": 3, "Bricklayer": 1},
)

dairy = BusinessArchetype(
    name="Dairy",
    owner_type="Milkman",
    employee_types={"Apprentice": 1, "Bottler": 1},
    max_instances=1,
    min_population=30,
)

day_care = BusinessArchetype(
    name="Daycare Service",
    owner_type="Daycare Provider",
    employee_types={"Daycare Provider": 2},
    min_population=200,
    max_instances=1,
)

deli = BusinessArchetype(
    name="Deli",
    owner_type="Proprietor",
    employee_types={"Cashier": 2, "Manager": 1},
    min_population=100,
    max_instances=2,
    services=["shopping"],
)

dentist_office = BusinessArchetype(
    name="Dentist Office",
    owner_type="Dentist",
    employee_types={"Nurse": 2, "Secretary": 1},
    min_population=75,
)

department_store = BusinessArchetype(
    name="Department Store",
    owner_type="Owner",
    employee_types={"Cashier": 2, "Manager": 1},
    min_population=200,
    max_instances=1,
    services=["shopping"],
)

diner = BusinessArchetype(
    name="Diner",
    owner_type="Proprietor",
    employee_types={"Cook": 1, "Waiter": 1, "Busboy": 1, "Manager": 1},
    year_available=1945,
    min_population=30,
    max_instances=3,
    services=["food", "socializing"],
)

distillery = BusinessArchetype(
    name="Distillery",
    owner_type="Distiller",
    employee_types={"Bottler": 1, "Cooper": 1},
    max_instances=1,
)

drug_store = BusinessArchetype(
    name="Drug Store",
    owner_type="Druggist",
    employee_types={"Cashier": 1},
    min_population=30,
    max_instances=1,
    services=["shopping"],
)

farm = BusinessArchetype(
    name="Farm", owner_type="Farmer", employee_types={"Farmhand": 2}, max_instances=99
)

fire_station = BusinessArchetype(
    name="Fire Station",
    employee_types={"Fire Chief": 1, "Fire Fighter": 2},
    min_population=100,
    max_instances=1,
)

foundry = BusinessArchetype(
    name="Foundry",
    owner_type="Owner",
    employee_types={"Molder": 1, "Puddler": 1},
    year_available=1830,
    year_obsolete=1950,
    min_population=20,
    max_instances=1,
)

furniture_store = BusinessArchetype(
    name="Furniture Store",
    owner_type="Woodworker",
    employee_types={"Apprentice": 1},
    min_population=20,
    max_instances=1,
    services=["shopping"],
)

general_store = BusinessArchetype(
    name="General Store",
    owner_type="Grocer",
    employee_types={"Manager": 1, "Stocker": 1, "Cashier": 1},
    min_population=20,
    max_instances=2,
    services=["shopping"],
)

grocery_store = BusinessArchetype(
    name="Grocery Store",
    owner_type="Grocer",
    employee_types={"Manager": 1, "Stocker": 1, "Cashier": 1},
    min_population=20,
    max_instances=2,
    services=["shopping"],
)

hardware_store = BusinessArchetype(
    name="Hardware Store",
    owner_type="Proprietor",
    employee_types={"Manager": 1, "Stocker": 1, "Cashier": 1},
    min_population=40,
    max_instances=2,
    services=["shopping"],
)

hospital = BusinessArchetype(
    name="Hospital",
    employee_types={"Doctor": 2, "Nurse": 1, "Secretary": 1},
    min_population=200,
)

hotel = BusinessArchetype(
    name="Hotel",
    owner_type="Owner",
    employee_types={"Hotel Maid": 2, "Concierge": 1, "Manager": 1},
)

inn = BusinessArchetype(
    name="Inn",
    owner_type="Innkeeper",
    employee_types={"Hotel Maid": 2, "Concierge": 1, "Manager": 1},
)

insurance_company = BusinessArchetype(
    name="Insurance Company",
    owner_type="Insurance Agent",
    employee_types={"Secretary": 1, "Insurance Agent": 2},
    max_instances=1,
)

jewelry_shop = BusinessArchetype(
    name="Jewelry Shop",
    owner_type="Jeweler",
    employee_types={"Cashier": 1, "Apprentice": 1},
    min_population=200,
    max_instances=1,
    services=["shopping"],
)

law_firm = BusinessArchetype(
    name="Law Firm",
    owner_type="Lawyer",
    employee_types={"Lawyer": 1, "Secretary": 1},
    min_population=150,
    max_instances=2,
)


optometry_clinic = BusinessArchetype(
    name="Optometry Clinic",
    owner_type="Optometrist",
    employee_types={"Secretary": 1, "Nurse": 1},
    year_available=1990,
)

painting_company = BusinessArchetype(
    name="Painting Company",
    owner_type="Painter",
    employee_types={"Painter": 1, "Plasterer": 1},
)

park = BusinessArchetype(
    name="Park",
    employee_types={"Groundskeeper": 1},
    min_population=100,
    max_instances=99,
    services=["shopping", "socializing", "recreation"],
)

pharmacy = BusinessArchetype(
    name="Pharmacy",
    owner_type="Pharmacist",
    employee_types={"Pharmacist": 1, "Cashier": 1},
    year_available=1960,
)

plastic_surgery_clinic = BusinessArchetype(
    name="Plastic Surgery Clinic",
    owner_type="Plastic Surgeon",
    employee_types={"Nurse": 1, "Secretary": 1},
    min_population=200,
    max_instances=1,
    year_available=1970,
)

plumbing_company = BusinessArchetype(
    name="Plumbing Company",
    owner_type="Plumber",
    employee_types={"Apprentice": 1, "Secretary": 1},
    min_population=100,
    max_instances=2,
)

police_station = BusinessArchetype(
    name="Police Station",
    employee_types={"Police Chief": 1, "Police Officer": 2},
    min_population=100,
    max_instances=1,
)

quarry = BusinessArchetype(
    name="Quarry",
    owner_type="Owner",
    employee_types={"Quarryman": 1, "Stone Cutter": 1, "Laborer": 1, "Engineer": 1},
    max_instances=1,
)

realty_firm = BusinessArchetype(
    name="Realty Firm",
    owner_type="Realtor",
    employee_types={"Realtor": 1, "Secretary": 1},
    min_population=80,
    max_instances=2,
)

restaurant = BusinessArchetype(
    name="Restaurant",
    owner_type="Proprietor",
    employee_types={"Waiter": 1, "Cook": 1, "Busboy": 1, "Manager": 1},
    min_population=50,
    services=["food", "socializing"],
)

school = BusinessArchetype(
    name="School",
    employee_types={"Principal": 1, "Teacher": 2, "Janitor": 1},
    max_instances=1,
)

shoemaker_shop = BusinessArchetype(
    name="Shoemaker Shop",
    owner_type="Shoemaker",
    employee_types={"Apprentice": 1},
    services=["shopping"],
)

supermarket = BusinessArchetype(
    name="Supermarket",
    owner_type="Owner",
    employee_types={"Cashier": 1, "Stocker": 1, "Manager": 1},
    min_population=200,
    max_instances=1,
    services=["shopping"],
)

tailor_shop = BusinessArchetype(
    name="Tailor Shop",
    owner_type="Tailor",
    employee_types={"Apprentice": 1},
    min_population=40,
    max_instances=1,
    services=["shopping"],
)

tattoo_parlor = BusinessArchetype(
    name="Tattoo Parlor",
    year_available=1970,
    min_population=300,
    max_instances=1,
    owner_type="Tattoo Artist",
    employee_types={"Cashier": 1},
    hours=["afternoon"],
)

tavern = BusinessArchetype(
    name="Tavern",
    hours=["evening", "night"],
    employee_types={"Cook": 1, "Bartender": 1, "Waiter": 1},
    min_population=20,
    services=["drinking", "socializing"],
)


taxi_depot = BusinessArchetype(
    name="Taxi Depot",
    owner_type="Proprietor",
    employee_types={"Taxi Driver": 3},
    max_instances=1,
    year_available=1930,
    year_obsolete=9999,
    hours=["day", "evening"],
)
