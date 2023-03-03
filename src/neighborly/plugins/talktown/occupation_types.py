"""
OccupationTypes adapted from Talk of the Town.

Sources:
https://github.com/ShiJbey/talktown/blob/python3/talktown/occupation.py
https://github.com/ShiJbey/talktown/blob/python3/talktown/config/businesses_config.py
"""

from neighborly.components.business import OccupationType
from neighborly.plugins.talktown.school import CollegeGraduate
from neighborly.utils.query import has_any_work_experience, has_work_experience_as

apprentice = OccupationType(name="Apprentice", level=1)

architect = OccupationType(
    name="Architect",
    level=4,
    rules=lambda gameobject: gameobject.has_component(CollegeGraduate),
)

bottler = OccupationType(
    name="Bottler",
    level=1,
)

bricklayer = OccupationType(
    name="Bricklayer",
    level=1,
)

builder = OccupationType(
    name="Builder",
    level=1,
)

cashier = OccupationType(
    name="Cashier",
    level=1,
)

cook = OccupationType(
    name="Cook",
    level=1,
)

dishwasher = OccupationType(
    name="Dishwasher",
    level=1,
)

groundskeeper = OccupationType(
    name="Groundskeeper",
    level=1,
)

hotel_maid = OccupationType(
    name="Hotel Maid",
    level=1,
)

janitor = OccupationType(
    name="Janitor",
    level=1,
)

laborer = OccupationType(
    name="Laborer",
    level=1,
)

secretary = OccupationType(
    name="Secretary",
    level=1,
)

waiter = OccupationType(
    name="Waiter",
    level=1,
)

whitewasher = OccupationType(
    name="Whitewasher",
    level=1,
)

busboy = OccupationType(
    name="Busboy",
    level=1,
)

stocker = OccupationType(
    name="Stocker",
    level=1,
)

seamstress = OccupationType(
    name="Seamstress",
    level=1,
)

farmer = OccupationType(
    name="Farmer",
    level=2,
)

farmhand = OccupationType(
    name="Farmhand",
    level=1,
)

miner = OccupationType(
    name="Miner",
    level=1,
)

painter = OccupationType(
    name="Painter",
    level=1,
)

banker = OccupationType(
    name="Banker",
    level=4,
)

bank_teller = OccupationType(
    name="Bank Teller",
    level=2,
)

grocer = OccupationType(
    name="Grocer",
    level=1,
)

bartender = OccupationType(
    name="Bartender",
    level=1,
)

concierge = OccupationType(
    name="Concierge",
    level=1,
)

daycare_provider = OccupationType(
    name="Daycare Provider",
    level=1,
)

landlord = OccupationType(
    name="Landlord",
    level=1,
)

baker = OccupationType(
    name="Baker",
    level=1,
)

cooper = OccupationType(
    name="Cooper",
    level=2,
)

barkeeper = OccupationType(
    name="Barkeeper",
    level=1,
)

milkman = OccupationType(
    name="Milkman",
    level=1,
)

plasterer = OccupationType(
    name="Plasterer",
    level=1,
)

barber = OccupationType(
    name="Barber",
    level=1,
)

butcher = OccupationType(
    name="Butcher",
    level=1,
)

fire_fighter = OccupationType(
    name="Fire Fighter",
    level=1,
)

carpenter = OccupationType(
    name="Carpenter",
    level=1,
)

taxi_driver = OccupationType(
    name="Taxi Driver",
    level=1,
)

bus_driver = OccupationType(
    name="Bus Driver",
    level=1,
)

blacksmith = OccupationType(
    name="Blacksmith",
    level=1,
)

woodworker = OccupationType(
    name="Woodworker",
    level=1,
)

stonecutter = OccupationType(
    name="Stone Cutter",
    level=1,
)

dressmaker = OccupationType(
    name="Dressmaker",
    level=1,
)

distiller = OccupationType(
    name="Distiller",
    level=1,
)

plumber = OccupationType(
    name="Plumber",
    level=1,
)

joiner = OccupationType(
    name="Joiner",
    level=1,
)

inn_keeper = OccupationType(
    name="Innkeeper",
    level=1,
)

nurse = OccupationType(
    name="Nurse",
    level=1,
)

shoemaker = OccupationType(
    name="Shoemaker",
    level=2,
)

brewer = OccupationType(
    name="Brewer",
    level=2,
)

tattoo_artist = OccupationType(
    name="Tattoo Artist",
    level=2,
)

puddler = OccupationType(
    name="Puddler",
    level=1,
)

clothier = OccupationType(
    name="Clothier",
    level=2,
)

teacher = OccupationType(
    name="Teacher",
    level=2,
)

principal = OccupationType(
    name="Principal", level=3, rules=has_work_experience_as("Teacher")
)

tailor = OccupationType(
    name="Tailor",
    level=2,
)

molder = OccupationType(
    name="Molder",
    level=2,
)

turner = OccupationType(
    name="Turner",
    level=2,
)

quarry_man = OccupationType(
    name="Quarryman",
    level=2,
)

proprietor = OccupationType(
    name="Proprietor",
    level=2,
)

dentist = OccupationType(
    name="Dentist",
    level=4,
    rules=lambda gameobject: gameobject.has_component(CollegeGraduate),
)

doctor = OccupationType(
    name="Doctor",
    level=4,
    rules=(
        has_any_work_experience(),
        lambda gameobject: gameobject.has_component(CollegeGraduate),
    ),
)

druggist = OccupationType(
    name="Druggist",
    level=3,
)

engineer = OccupationType(
    name="Engineer",
    level=4,
    rules=lambda gameobject: gameobject.has_component(CollegeGraduate),
)

fire_chief = OccupationType(
    name="Fire Chief",
    level=3,
    rules=has_work_experience_as("Fire Fighter"),
)

insurance_agent = OccupationType(
    name="Insurance Agent",
    level=3,
)

jeweler = OccupationType(
    name="Jeweler",
    level=3,
)

lawyer = OccupationType(
    name="Lawyer",
    level=4,
    rules=(
        has_any_work_experience(),
        lambda gameobject: gameobject.has_component(CollegeGraduate),
    ),
)

manager = OccupationType(
    name="Manager",
    level=2,
)

mayor = OccupationType(
    name="Mayor",
    level=5,
)

mortician = OccupationType(
    name="Mortician",
    level=3,
)

owner = OccupationType(
    name="Owner",
    level=5,
)

professor = OccupationType(
    name="Professor",
    level=4,
    rules=lambda gameobject: gameobject.has_component(CollegeGraduate),
)

optometrist = OccupationType(
    name="Optometrist",
    level=4,
    rules=lambda gameobject: gameobject.has_component(CollegeGraduate),
)

pharmacist = OccupationType(
    name="Pharmacist",
    level=4,
    rules=lambda gameobject: gameobject.has_component(CollegeGraduate),
)

plastic_surgeon = OccupationType(
    name="Plastic Surgeon",
    level=4,
    rules=(
        has_any_work_experience(),
        lambda gameobject: gameobject.has_component(CollegeGraduate),
    ),
)

police_chief = OccupationType(
    name="Police Chief",
    level=3,
    rules=has_work_experience_as("Police Chief"),
)

police_officer = OccupationType(
    name="Police Officer",
    level=1,
    rules=has_work_experience_as("Police Officer"),
)

realtor = OccupationType(
    name="Realtor",
    level=3,
)
