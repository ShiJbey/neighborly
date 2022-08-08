"""
OccupationTypes adapted from Talk of the Town.

Sources:
https://github.com/ShiJbey/talktown/blob/python3/talktown/occupation.py
https://github.com/ShiJbey/talktown/blob/python3/talktown/config/businesses_config.py
"""

from neighborly.builtin.helpers import (
    after_year,
    has_any_work_experience,
    has_experience_as_a,
    is_college_graduate,
    is_gender,
)
from neighborly.core.business import (
    OccupationType,
    join_preconditions,
    or_preconditions,
)

apprentice = OccupationType(name="Apprentice", level=1, precondition=is_gender("male"))

architect = OccupationType(
    name="Architect",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1977)), is_college_graduate()
    ),
)

bottler = OccupationType(
    name="Bottler",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1943)),
)

bricklayer = OccupationType(
    name="Bricklayer",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

builder = OccupationType(
    name="Builder",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

cashier = OccupationType(
    name="Cashier",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1917)),
)

cook = OccupationType(
    name="Cook",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1966)),
)

dishwasher = OccupationType(
    name="Dishwasher",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1966)),
)

groundskeeper = OccupationType(
    name="Groundskeeper",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)


hotel_maid = OccupationType(
    name="Hotel Maid",
    level=1,
    precondition=is_gender("female"),
)

janitor = OccupationType(
    name="Janitor",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1966)),
)

laborer = OccupationType(
    name="Laborer",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

secretary = OccupationType(
    name="Secretary",
    level=1,
    precondition=or_preconditions(is_gender("female")),
)

waiter = OccupationType(
    name="Waiter",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1917)),
)


whitewasher = OccupationType(
    name="Whitewasher",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)


busboy = OccupationType(
    name="Busboy",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

stocker = OccupationType(
    name="Stocker",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1943)),
)

seamstress = OccupationType(
    name="Waiter",
    level=1,
    precondition=or_preconditions(is_gender("female")),
)

farmer = OccupationType(
    name="Farmer",
    level=2,
    precondition=or_preconditions(is_gender("male")),
)

farmhand = OccupationType(
    name="Farmhand",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

miner = OccupationType(
    name="Miner",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

painter = OccupationType(
    name="Painter",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

banker = OccupationType(
    name="Banker",
    level=4,
    precondition=or_preconditions(is_gender("male"), after_year(1968)),
)

bank_teller = OccupationType(
    name="Bank Teller",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1950)),
)

grocer = OccupationType(
    name="Grocer",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1966)),
)

bartender = OccupationType(
    name="Bartender",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1968)),
)

concierge = OccupationType(
    name="Concierge",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1968)),
)

daycare_provider = OccupationType(
    name="Daycare Provider",
    level=1,
    precondition=or_preconditions(is_gender("female"), after_year(1977)),
)

landlord = OccupationType(
    name="Landlord",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1925)),
)

baker = OccupationType(
    name="Baker",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1935)),
)

cooper = OccupationType(
    name="Cooper",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

barkeeper = OccupationType(
    name="Barkeeper",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

milkman = OccupationType(
    name="Milkman",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

plasterer = OccupationType(
    name="Plasterer",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

barber = OccupationType(
    name="Barber",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

butcher = OccupationType(
    name="Butcher",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

fire_fighter = OccupationType(
    name="Fire Fighter",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

carpenter = OccupationType(
    name="Carpenter",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

taxi_driver = OccupationType(
    name="Taxi Driver",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

bus_driver = OccupationType(
    name="Bus Driver",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1972)),
)

blacksmith = OccupationType(
    name="Blacksmith",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

woodworker = OccupationType(
    name="Woodworker",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

stonecutter = OccupationType(
    name="Stonecutter",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

dressmaker = OccupationType(
    name="Dressmaker",
    level=1,
    precondition=or_preconditions(is_gender("female"), after_year(1972)),
)

distiller = OccupationType(
    name="Distiller",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

plumber = OccupationType(
    name="Plumber",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

joiner = OccupationType(
    name="Joiner",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

inn_keeper = OccupationType(
    name="Innkeeper",
    level=1,
    precondition=or_preconditions(is_gender("male"), after_year(1928)),
)

nurse = OccupationType(
    name="Nurse",
    level=1,
    precondition=or_preconditions(is_gender("female"), after_year(1977)),
)

shoemaker = OccupationType(
    name="Shoemaker",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1960)),
)

brewer = OccupationType(
    name="Brewer",
    level=2,
    precondition=or_preconditions(is_gender("male")),
)

tattoo_artist = OccupationType(
    name="Tattoo Artist",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1972)),
)

puddler = OccupationType(
    name="Puddler",
    level=1,
    precondition=or_preconditions(is_gender("male")),
)

clothier = OccupationType(
    name="Clothier",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1930)),
)

teacher = OccupationType(
    name="Teacher",
    level=2,
    precondition=or_preconditions(is_gender("female"), after_year(1955)),
)

principal = OccupationType(
    name="Principal",
    level=3,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1965)),
        has_experience_as_a("Teacher"),
    ),
)

tailor = OccupationType(
    name="Tailor",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1955)),
)

molder = OccupationType(
    name="Molder",
    level=2,
    precondition=or_preconditions(is_gender("male")),
)

turner = OccupationType(
    name="Turner",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

quarry_man = OccupationType(
    name="Quarryman",
    level=2,
    precondition=or_preconditions(is_gender("male")),
)

proprietor = OccupationType(
    name="Proprietor",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1955)),
)


dentist = OccupationType(
    name="Dentist",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1972)), is_college_graduate()
    ),
)

doctor = OccupationType(
    name="Doctor",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1972)),
        has_any_work_experience(),
        is_college_graduate(),
    ),
)

druggist = OccupationType(
    name="Druggist",
    level=3,
    precondition=or_preconditions(is_gender("male")),
)

engineer = OccupationType(
    name="Engineer",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1977)), is_college_graduate()
    ),
)

fire_chief = OccupationType(
    name="Fire Chief",
    level=3,
    precondition=join_preconditions(
        is_gender("male"), has_experience_as_a("Fire Fighter")
    ),
)

insurance_agent = OccupationType(
    name="Insurance Agent",
    level=3,
    precondition=or_preconditions(is_gender("male"), after_year(1972)),
)

jeweler = OccupationType(
    name="Jeweler",
    level=3,
    precondition=or_preconditions(is_gender("male"), after_year(1972)),
)


lawyer = OccupationType(
    name="Lawyer",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1977)),
        has_any_work_experience(),
        is_college_graduate(),
    ),
)

manager = OccupationType(
    name="Manager",
    level=2,
    precondition=or_preconditions(is_gender("male"), after_year(1972)),
)

mayor = OccupationType(
    name="Mayor",
    level=5,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

mortician = OccupationType(
    name="Mortician",
    level=3,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

owner = OccupationType(
    name="Owner",
    level=5,
    precondition=or_preconditions(is_gender("male"), after_year(1977)),
)

professor = OccupationType(
    name="Professor",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1962)), is_college_graduate()
    ),
)

optometrist = OccupationType(
    name="Optometrist",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1972)), is_college_graduate()
    ),
)


pharmacist = OccupationType(
    name="Pharmacist",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1972)), is_college_graduate()
    ),
)

plastic_surgeon = OccupationType(
    name="Plastic Surgeon",
    level=4,
    precondition=join_preconditions(
        or_preconditions(is_gender("male"), after_year(1972)),
        has_any_work_experience(),
        is_college_graduate(),
    ),
)

police_chief = OccupationType(
    name="Police Chief",
    level=3,
    precondition=join_preconditions(
        is_gender("male"), has_experience_as_a("Police Officer")
    ),
)


realtor = OccupationType(
    name="Realtor",
    level=3,
    precondition=or_preconditions(is_gender("male"), after_year(1966)),
)
