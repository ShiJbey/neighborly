import logging
import os
import pathlib

import neighborly.plugins.talktown.business_archetypes as tot_businesses
import neighborly.plugins.talktown.occupation_types as tot_occupations
from neighborly.core.archetypes import (
    BusinessArchetypeLibrary,
    CharacterArchetype,
    CharacterArchetypeLibrary,
    ResidenceArchetype,
    ResidenceArchetypeLibrary,
)
from neighborly.core.business import OccupationTypeLibrary
from neighborly.core.ecs import World
from neighborly.core.rng import DefaultRNG
from neighborly.core.town import LandGrid
from neighborly.plugins.talktown.school import SchoolSystem
from neighborly.simulation import Plugin, Simulation

logger = logging.getLogger(__name__)

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent


def establish_town(world: World, **kwargs) -> None:
    """
    Adds an initial set of families and businesses
    to the start of the town.

    This system runs once, then removes itself from
    the ECS to free resources.

    Parameters
    ----------
    world : World
        The world instance of the simulation

    Notes
    -----
    This function is based on the original Simulation.establish_setting
    method in talktown.
    """
    vacant_lots = town.get_component(LandGrid).layout.get_vacancies()
    # Each family requires 2 lots (1 for a house, 1 for a business)
    # Save two lots for either a coalmine, quarry, or farm
    n_families_to_add = (len(vacant_lots) // 2) - 1

    for _ in range(n_families_to_add - 1):
        # create residents
        house = world.spawn_archetype(ResidenceArchetypeLibrary.get("House"))
        # create Farm
        farm = world.spawn_archetype(BusinessArchetypeLibrary.get("Farm"))
        # trigger hiring event
        # trigger home move event

    random_num = world.get_resource(DefaultRNG).random()
    if random_num < 0.2:
        # Create a Coalmine 20% of the time
        coal_mine = world.spawn_archetype(BusinessArchetypeLibrary.get("Coal Mine"))
    elif 0.2 <= random_num < 0.35:
        # Create a Quarry 15% of the time
        quarry = world.spawn_archetype(BusinessArchetypeLibrary.get("Quarry"))
    else:
        # Create Farm 65% of the time
        farm = world.spawn_archetype(BusinessArchetypeLibrary.get("Farm"))

    logger.debug("Town established. 'establish_town' function removed from systems")


class TalkOfTheTownPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        sim.world.add_system(SchoolSystem())

        # Talk of the town only has one residence archetype
        ResidenceArchetypeLibrary.add(ResidenceArchetype(name="House"))

        # Talk of the town only has one entity archetype
        CharacterArchetypeLibrary.add(
            CharacterArchetype(
                name="Person",
                name_format="#first_name# #family_name#",
                lifespan=85,
                life_stages={
                    "child": 0,
                    "teen": 13,
                    "young_adult": 18,
                    "adult": 30,
                    "elder": 65,
                },
            )
        )

        # Register OccupationTypes
        OccupationTypeLibrary.add(tot_occupations.apprentice)
        OccupationTypeLibrary.add(tot_occupations.architect)
        OccupationTypeLibrary.add(tot_occupations.baker)
        OccupationTypeLibrary.add(tot_occupations.banker)
        OccupationTypeLibrary.add(tot_occupations.bank_teller)
        OccupationTypeLibrary.add(tot_occupations.barber)
        OccupationTypeLibrary.add(tot_occupations.barkeeper)
        OccupationTypeLibrary.add(tot_occupations.bartender)
        OccupationTypeLibrary.add(tot_occupations.bottler)
        OccupationTypeLibrary.add(tot_occupations.blacksmith)
        OccupationTypeLibrary.add(tot_occupations.brewer)
        OccupationTypeLibrary.add(tot_occupations.bricklayer)
        OccupationTypeLibrary.add(tot_occupations.builder)
        OccupationTypeLibrary.add(tot_occupations.busboy)
        OccupationTypeLibrary.add(tot_occupations.bus_driver)
        OccupationTypeLibrary.add(tot_occupations.butcher)
        OccupationTypeLibrary.add(tot_occupations.carpenter)
        OccupationTypeLibrary.add(tot_occupations.cashier)
        OccupationTypeLibrary.add(tot_occupations.clothier)
        OccupationTypeLibrary.add(tot_occupations.concierge)
        OccupationTypeLibrary.add(tot_occupations.cook)
        OccupationTypeLibrary.add(tot_occupations.cooper)
        OccupationTypeLibrary.add(tot_occupations.daycare_provider)
        OccupationTypeLibrary.add(tot_occupations.dentist)
        OccupationTypeLibrary.add(tot_occupations.dishwasher)
        OccupationTypeLibrary.add(tot_occupations.distiller)
        OccupationTypeLibrary.add(tot_occupations.doctor)
        OccupationTypeLibrary.add(tot_occupations.dressmaker)
        OccupationTypeLibrary.add(tot_occupations.druggist)
        OccupationTypeLibrary.add(tot_occupations.engineer)
        OccupationTypeLibrary.add(tot_occupations.farmer)
        OccupationTypeLibrary.add(tot_occupations.farmhand)
        OccupationTypeLibrary.add(tot_occupations.fire_chief)
        OccupationTypeLibrary.add(tot_occupations.fire_fighter)
        OccupationTypeLibrary.add(tot_occupations.grocer)
        OccupationTypeLibrary.add(tot_occupations.groundskeeper)
        OccupationTypeLibrary.add(tot_occupations.hotel_maid)
        OccupationTypeLibrary.add(tot_occupations.inn_keeper)
        OccupationTypeLibrary.add(tot_occupations.insurance_agent)
        OccupationTypeLibrary.add(tot_occupations.janitor)
        OccupationTypeLibrary.add(tot_occupations.jeweler)
        OccupationTypeLibrary.add(tot_occupations.joiner)
        OccupationTypeLibrary.add(tot_occupations.laborer)
        OccupationTypeLibrary.add(tot_occupations.landlord)
        OccupationTypeLibrary.add(tot_occupations.lawyer)
        OccupationTypeLibrary.add(tot_occupations.manager)
        OccupationTypeLibrary.add(tot_occupations.miner)
        OccupationTypeLibrary.add(tot_occupations.milkman)
        OccupationTypeLibrary.add(tot_occupations.mayor)
        OccupationTypeLibrary.add(tot_occupations.molder)
        OccupationTypeLibrary.add(tot_occupations.mortician)
        OccupationTypeLibrary.add(tot_occupations.nurse)
        OccupationTypeLibrary.add(tot_occupations.optometrist)
        OccupationTypeLibrary.add(tot_occupations.owner)
        OccupationTypeLibrary.add(tot_occupations.painter)
        OccupationTypeLibrary.add(tot_occupations.pharmacist)
        OccupationTypeLibrary.add(tot_occupations.plasterer)
        OccupationTypeLibrary.add(tot_occupations.plastic_surgeon)
        OccupationTypeLibrary.add(tot_occupations.plumber)
        OccupationTypeLibrary.add(tot_occupations.police_chief)
        OccupationTypeLibrary.add(tot_occupations.principal)
        OccupationTypeLibrary.add(tot_occupations.professor)
        OccupationTypeLibrary.add(tot_occupations.proprietor)
        OccupationTypeLibrary.add(tot_occupations.puddler)
        OccupationTypeLibrary.add(tot_occupations.quarry_man)
        OccupationTypeLibrary.add(tot_occupations.realtor)
        OccupationTypeLibrary.add(tot_occupations.seamstress)
        OccupationTypeLibrary.add(tot_occupations.secretary)
        OccupationTypeLibrary.add(tot_occupations.stocker)
        OccupationTypeLibrary.add(tot_occupations.shoemaker)
        OccupationTypeLibrary.add(tot_occupations.stonecutter)
        OccupationTypeLibrary.add(tot_occupations.tailor)
        OccupationTypeLibrary.add(tot_occupations.tattoo_artist)
        OccupationTypeLibrary.add(tot_occupations.taxi_driver)
        OccupationTypeLibrary.add(tot_occupations.teacher)
        OccupationTypeLibrary.add(tot_occupations.turner)
        OccupationTypeLibrary.add(tot_occupations.waiter)
        OccupationTypeLibrary.add(tot_occupations.whitewasher)
        OccupationTypeLibrary.add(tot_occupations.woodworker)

        # Register Business Archetypes
        BusinessArchetypeLibrary.add(tot_businesses.apartment_complex)
        BusinessArchetypeLibrary.add(tot_businesses.bakery)
        BusinessArchetypeLibrary.add(tot_businesses.bank)
        BusinessArchetypeLibrary.add(tot_businesses.bar)
        BusinessArchetypeLibrary.add(tot_businesses.barbershop)
        BusinessArchetypeLibrary.add(tot_businesses.bus_depot)
        BusinessArchetypeLibrary.add(tot_businesses.carpentry_company)
        BusinessArchetypeLibrary.add(tot_businesses.cemetery)
        BusinessArchetypeLibrary.add(tot_businesses.city_hall)
        BusinessArchetypeLibrary.add(tot_businesses.clothing_store)
        BusinessArchetypeLibrary.add(tot_businesses.coal_mine)
        BusinessArchetypeLibrary.add(tot_businesses.construction_firm)
        BusinessArchetypeLibrary.add(tot_businesses.dairy)
        BusinessArchetypeLibrary.add(tot_businesses.day_care)
        BusinessArchetypeLibrary.add(tot_businesses.deli)
        BusinessArchetypeLibrary.add(tot_businesses.dentist_office)
        BusinessArchetypeLibrary.add(tot_businesses.department_store)
        BusinessArchetypeLibrary.add(tot_businesses.diner)
        BusinessArchetypeLibrary.add(tot_businesses.distillery)
        BusinessArchetypeLibrary.add(tot_businesses.drug_store)
        BusinessArchetypeLibrary.add(tot_businesses.farm)
        BusinessArchetypeLibrary.add(tot_businesses.fire_station)
        BusinessArchetypeLibrary.add(tot_businesses.foundry)
        BusinessArchetypeLibrary.add(tot_businesses.furniture_store)
        BusinessArchetypeLibrary.add(tot_businesses.general_store)
        BusinessArchetypeLibrary.add(tot_businesses.grocery_store)
        BusinessArchetypeLibrary.add(tot_businesses.hardware_store)
        BusinessArchetypeLibrary.add(tot_businesses.hospital)
        BusinessArchetypeLibrary.add(tot_businesses.hotel)
        BusinessArchetypeLibrary.add(tot_businesses.inn)
        BusinessArchetypeLibrary.add(tot_businesses.insurance_company)
        BusinessArchetypeLibrary.add(tot_businesses.jewelry_shop)
        BusinessArchetypeLibrary.add(tot_businesses.law_firm)
        BusinessArchetypeLibrary.add(tot_businesses.optometry_clinic)
        BusinessArchetypeLibrary.add(tot_businesses.painting_company)
        BusinessArchetypeLibrary.add(tot_businesses.park)
        BusinessArchetypeLibrary.add(tot_businesses.pharmacy)
        BusinessArchetypeLibrary.add(tot_businesses.plastic_surgery_clinic)
        BusinessArchetypeLibrary.add(tot_businesses.plumbing_company)
        BusinessArchetypeLibrary.add(tot_businesses.police_station)
        BusinessArchetypeLibrary.add(tot_businesses.quarry)
        BusinessArchetypeLibrary.add(tot_businesses.realty_firm)
        BusinessArchetypeLibrary.add(tot_businesses.restaurant)
        BusinessArchetypeLibrary.add(tot_businesses.school)
        BusinessArchetypeLibrary.add(tot_businesses.shoemaker_shop)
        BusinessArchetypeLibrary.add(tot_businesses.supermarket)
        BusinessArchetypeLibrary.add(tot_businesses.tailor_shop)
        BusinessArchetypeLibrary.add(tot_businesses.tattoo_parlor)
        BusinessArchetypeLibrary.add(tot_businesses.tavern)
        BusinessArchetypeLibrary.add(tot_businesses.taxi_depot)


def get_plugin() -> Plugin:
    return TalkOfTheTownPlugin()
