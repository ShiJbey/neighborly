import logging
import os
import pathlib

import neighborly.plugins.talktown.business_archetypes as tot_businesses
import neighborly.plugins.talktown.occupation_types as tot_occupations
from neighborly.builtin.archetypes import HumanArchetype
from neighborly.core.archetypes import (
    BaseCharacterArchetype,
    BaseResidenceArchetype,
    BusinessArchetypes,
    CharacterArchetypes,
    ResidenceArchetypes,
)
from neighborly.core.business import OccupationTypes
from neighborly.core.ecs import ISystem, World
from neighborly.core.rng import DefaultRNG
from neighborly.core.town import LandGrid
from neighborly.plugins.talktown.school import SchoolSystem
from neighborly.simulation import Plugin, Simulation

logger = logging.getLogger(__name__)

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent


class EstablishTownSystem(ISystem):
    def process(self, world: World, **kwargs) -> None:
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
            house = ResidenceArchetypes.get("House").create(self.world)
            # create Farm
            farm = BusinessArchetypes.get("Farm").create(self.world)
            # trigger hiring event
            # trigger home move event

        random_num = world.get_resource(DefaultRNG).random()
        if random_num < 0.2:
            # Create a Coalmine 20% of the time
            coal_mine = BusinessArchetypes.get("Coal Mine").create(self.world)
        elif 0.2 <= random_num < 0.35:
            # Create a Quarry 15% of the time
            quarry = BusinessArchetypes.get("Quarry").create(self.world)
        else:
            # Create Farm 65% of the time
            farm = BusinessArchetypes.get("Farm").create(self.world)

        self.world.remove_system(type(self))
        logger.debug("Town established. 'establish_town' function removed from systems")


class TalkOfTheTownPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        sim.world.add_system(SchoolSystem())

        # Talk of the town only has one residence archetype
        ResidenceArchetypes.add("House", BaseResidenceArchetype())

        # Talk of the town only has one entity archetype
        CharacterArchetypes.add(
            "Person",
            HumanArchetype(
                life_stage_ages={
                    "child": 0,
                    "teen": 13,
                    "young_adult": 18,
                    "adult": 30,
                    "elder": 65,
                },
                chance_spawn_with_spouse=1.0,
                max_children_at_spawn=3,
            ),
        )

        # Register OccupationTypes
        OccupationTypes.add(tot_occupations.apprentice)
        OccupationTypes.add(tot_occupations.architect)
        OccupationTypes.add(tot_occupations.baker)
        OccupationTypes.add(tot_occupations.banker)
        OccupationTypes.add(tot_occupations.bank_teller)
        OccupationTypes.add(tot_occupations.barber)
        OccupationTypes.add(tot_occupations.barkeeper)
        OccupationTypes.add(tot_occupations.bartender)
        OccupationTypes.add(tot_occupations.bottler)
        OccupationTypes.add(tot_occupations.blacksmith)
        OccupationTypes.add(tot_occupations.brewer)
        OccupationTypes.add(tot_occupations.bricklayer)
        OccupationTypes.add(tot_occupations.builder)
        OccupationTypes.add(tot_occupations.busboy)
        OccupationTypes.add(tot_occupations.bus_driver)
        OccupationTypes.add(tot_occupations.butcher)
        OccupationTypes.add(tot_occupations.carpenter)
        OccupationTypes.add(tot_occupations.cashier)
        OccupationTypes.add(tot_occupations.clothier)
        OccupationTypes.add(tot_occupations.concierge)
        OccupationTypes.add(tot_occupations.cook)
        OccupationTypes.add(tot_occupations.cooper)
        OccupationTypes.add(tot_occupations.daycare_provider)
        OccupationTypes.add(tot_occupations.dentist)
        OccupationTypes.add(tot_occupations.dishwasher)
        OccupationTypes.add(tot_occupations.distiller)
        OccupationTypes.add(tot_occupations.doctor)
        OccupationTypes.add(tot_occupations.dressmaker)
        OccupationTypes.add(tot_occupations.druggist)
        OccupationTypes.add(tot_occupations.engineer)
        OccupationTypes.add(tot_occupations.farmer)
        OccupationTypes.add(tot_occupations.farmhand)
        OccupationTypes.add(tot_occupations.fire_chief)
        OccupationTypes.add(tot_occupations.fire_fighter)
        OccupationTypes.add(tot_occupations.grocer)
        OccupationTypes.add(tot_occupations.groundskeeper)
        OccupationTypes.add(tot_occupations.hotel_maid)
        OccupationTypes.add(tot_occupations.inn_keeper)
        OccupationTypes.add(tot_occupations.insurance_agent)
        OccupationTypes.add(tot_occupations.janitor)
        OccupationTypes.add(tot_occupations.jeweler)
        OccupationTypes.add(tot_occupations.joiner)
        OccupationTypes.add(tot_occupations.laborer)
        OccupationTypes.add(tot_occupations.landlord)
        OccupationTypes.add(tot_occupations.lawyer)
        OccupationTypes.add(tot_occupations.manager)
        OccupationTypes.add(tot_occupations.miner)
        OccupationTypes.add(tot_occupations.milkman)
        OccupationTypes.add(tot_occupations.mayor)
        OccupationTypes.add(tot_occupations.molder)
        OccupationTypes.add(tot_occupations.mortician)
        OccupationTypes.add(tot_occupations.nurse)
        OccupationTypes.add(tot_occupations.optometrist)
        OccupationTypes.add(tot_occupations.owner)
        OccupationTypes.add(tot_occupations.painter)
        OccupationTypes.add(tot_occupations.pharmacist)
        OccupationTypes.add(tot_occupations.plasterer)
        OccupationTypes.add(tot_occupations.plastic_surgeon)
        OccupationTypes.add(tot_occupations.plumber)
        OccupationTypes.add(tot_occupations.police_chief)
        OccupationTypes.add(tot_occupations.police_officer)
        OccupationTypes.add(tot_occupations.principal)
        OccupationTypes.add(tot_occupations.professor)
        OccupationTypes.add(tot_occupations.proprietor)
        OccupationTypes.add(tot_occupations.puddler)
        OccupationTypes.add(tot_occupations.quarry_man)
        OccupationTypes.add(tot_occupations.realtor)
        OccupationTypes.add(tot_occupations.seamstress)
        OccupationTypes.add(tot_occupations.secretary)
        OccupationTypes.add(tot_occupations.stocker)
        OccupationTypes.add(tot_occupations.shoemaker)
        OccupationTypes.add(tot_occupations.stonecutter)
        OccupationTypes.add(tot_occupations.tailor)
        OccupationTypes.add(tot_occupations.tattoo_artist)
        OccupationTypes.add(tot_occupations.taxi_driver)
        OccupationTypes.add(tot_occupations.teacher)
        OccupationTypes.add(tot_occupations.turner)
        OccupationTypes.add(tot_occupations.waiter)
        OccupationTypes.add(tot_occupations.whitewasher)
        OccupationTypes.add(tot_occupations.woodworker)

        # Register Business Archetypes
        BusinessArchetypes.add("Bakery", tot_businesses.bakery)
        BusinessArchetypes.add("Bank", tot_businesses.bank)
        BusinessArchetypes.add("Bar", tot_businesses.bar)
        BusinessArchetypes.add("BarberShop", tot_businesses.barbershop)
        BusinessArchetypes.add("BusDepot", tot_businesses.bus_depot)
        BusinessArchetypes.add("CarpentryCompany", tot_businesses.carpentry_company)
        BusinessArchetypes.add("Cemetery", tot_businesses.cemetery)
        BusinessArchetypes.add("CityHall", tot_businesses.city_hall)
        BusinessArchetypes.add("ClothingStore", tot_businesses.clothing_store)
        BusinessArchetypes.add("CoalMine", tot_businesses.coal_mine)
        BusinessArchetypes.add("ConstructionFirm", tot_businesses.construction_firm)
        BusinessArchetypes.add("Dairy", tot_businesses.dairy)
        BusinessArchetypes.add("DayCare", tot_businesses.day_care)
        BusinessArchetypes.add("Deli", tot_businesses.deli)
        BusinessArchetypes.add("DentistOffice", tot_businesses.dentist_office)
        BusinessArchetypes.add("DepartmentStore", tot_businesses.department_store)
        BusinessArchetypes.add("Dinner", tot_businesses.diner)
        BusinessArchetypes.add("Distillery", tot_businesses.distillery)
        BusinessArchetypes.add("DrugStore", tot_businesses.drug_store)
        BusinessArchetypes.add("Farm", tot_businesses.farm)
        BusinessArchetypes.add("FireStation", tot_businesses.fire_station)
        BusinessArchetypes.add("Foundry", tot_businesses.foundry)
        BusinessArchetypes.add("FurnitureStore", tot_businesses.furniture_store)
        BusinessArchetypes.add("GeneralStore", tot_businesses.general_store)
        BusinessArchetypes.add("GroceryStore", tot_businesses.grocery_store)
        BusinessArchetypes.add("HardwareStore", tot_businesses.hardware_store)
        BusinessArchetypes.add("Hospital", tot_businesses.hospital)
        BusinessArchetypes.add("Hotel", tot_businesses.hotel)
        BusinessArchetypes.add("Inn", tot_businesses.inn)
        BusinessArchetypes.add("InsuranceCompany", tot_businesses.insurance_company)
        BusinessArchetypes.add("JewelryShop", tot_businesses.jewelry_shop)
        BusinessArchetypes.add("LawFirm", tot_businesses.law_firm)
        BusinessArchetypes.add("OptometryClinic", tot_businesses.optometry_clinic)
        BusinessArchetypes.add("PaintingCompany", tot_businesses.painting_company)
        BusinessArchetypes.add("Park", tot_businesses.park)
        BusinessArchetypes.add("Pharmacy", tot_businesses.pharmacy)
        BusinessArchetypes.add(
            "PlasticSurgeryClinic", tot_businesses.plastic_surgery_clinic
        )
        BusinessArchetypes.add("PlumbingCompany", tot_businesses.plumbing_company)
        BusinessArchetypes.add("PoliceStation", tot_businesses.police_station)
        BusinessArchetypes.add("Quarry", tot_businesses.quarry)
        BusinessArchetypes.add("RealtyFirm", tot_businesses.realty_firm)
        BusinessArchetypes.add("Restaurant", tot_businesses.restaurant)
        BusinessArchetypes.add("School", tot_businesses.school)
        BusinessArchetypes.add("ShoemakerShop", tot_businesses.shoemaker_shop)
        BusinessArchetypes.add("SuperMarket", tot_businesses.supermarket)
        BusinessArchetypes.add("TailorShop", tot_businesses.tailor_shop)
        BusinessArchetypes.add("TattooParlor", tot_businesses.tattoo_parlor)
        BusinessArchetypes.add("Tavern", tot_businesses.tavern)
        BusinessArchetypes.add("TaxiDepot", tot_businesses.taxi_depot)


def get_plugin() -> Plugin:
    return TalkOfTheTownPlugin()
