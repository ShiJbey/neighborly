import logging
import os
import pathlib
from typing import Any

import neighborly.plugins.talktown.business_archetypes as tot_businesses
import neighborly.plugins.talktown.occupation_types as tot_occupations
from neighborly.archetypes import BaseResidenceArchetype, HumanArchetype
from neighborly.plugins.talktown.school import SchoolSystem
from neighborly.simulation import Plugin, Simulation

logger = logging.getLogger(__name__)

_RESOURCES_DIR = pathlib.Path(os.path.abspath(__file__)).parent


class TalkOfTheTownPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs: Any) -> None:
        sim.world.add_system(SchoolSystem())

        # Talk of the town only has one residence archetype
        sim.engine.residence_archetypes.add("House", BaseResidenceArchetype())

        # Talk of the town only has one entity archetype
        sim.engine.character_archetypes.add(
            "Person",
            HumanArchetype(
                chance_spawn_with_spouse=1.0,
                max_children_at_spawn=3,
            ),
        )

        # Register OccupationTypes
        sim.engine.occupation_types.add(tot_occupations.apprentice)
        sim.engine.occupation_types.add(tot_occupations.architect)
        sim.engine.occupation_types.add(tot_occupations.baker)
        sim.engine.occupation_types.add(tot_occupations.banker)
        sim.engine.occupation_types.add(tot_occupations.bank_teller)
        sim.engine.occupation_types.add(tot_occupations.barber)
        sim.engine.occupation_types.add(tot_occupations.barkeeper)
        sim.engine.occupation_types.add(tot_occupations.bartender)
        sim.engine.occupation_types.add(tot_occupations.bottler)
        sim.engine.occupation_types.add(tot_occupations.blacksmith)
        sim.engine.occupation_types.add(tot_occupations.brewer)
        sim.engine.occupation_types.add(tot_occupations.bricklayer)
        sim.engine.occupation_types.add(tot_occupations.builder)
        sim.engine.occupation_types.add(tot_occupations.busboy)
        sim.engine.occupation_types.add(tot_occupations.bus_driver)
        sim.engine.occupation_types.add(tot_occupations.butcher)
        sim.engine.occupation_types.add(tot_occupations.carpenter)
        sim.engine.occupation_types.add(tot_occupations.cashier)
        sim.engine.occupation_types.add(tot_occupations.clothier)
        sim.engine.occupation_types.add(tot_occupations.concierge)
        sim.engine.occupation_types.add(tot_occupations.cook)
        sim.engine.occupation_types.add(tot_occupations.cooper)
        sim.engine.occupation_types.add(tot_occupations.daycare_provider)
        sim.engine.occupation_types.add(tot_occupations.dentist)
        sim.engine.occupation_types.add(tot_occupations.dishwasher)
        sim.engine.occupation_types.add(tot_occupations.distiller)
        sim.engine.occupation_types.add(tot_occupations.doctor)
        sim.engine.occupation_types.add(tot_occupations.dressmaker)
        sim.engine.occupation_types.add(tot_occupations.druggist)
        sim.engine.occupation_types.add(tot_occupations.engineer)
        sim.engine.occupation_types.add(tot_occupations.farmer)
        sim.engine.occupation_types.add(tot_occupations.farmhand)
        sim.engine.occupation_types.add(tot_occupations.fire_chief)
        sim.engine.occupation_types.add(tot_occupations.fire_fighter)
        sim.engine.occupation_types.add(tot_occupations.grocer)
        sim.engine.occupation_types.add(tot_occupations.groundskeeper)
        sim.engine.occupation_types.add(tot_occupations.hotel_maid)
        sim.engine.occupation_types.add(tot_occupations.inn_keeper)
        sim.engine.occupation_types.add(tot_occupations.insurance_agent)
        sim.engine.occupation_types.add(tot_occupations.janitor)
        sim.engine.occupation_types.add(tot_occupations.jeweler)
        sim.engine.occupation_types.add(tot_occupations.joiner)
        sim.engine.occupation_types.add(tot_occupations.laborer)
        sim.engine.occupation_types.add(tot_occupations.landlord)
        sim.engine.occupation_types.add(tot_occupations.lawyer)
        sim.engine.occupation_types.add(tot_occupations.manager)
        sim.engine.occupation_types.add(tot_occupations.miner)
        sim.engine.occupation_types.add(tot_occupations.milkman)
        sim.engine.occupation_types.add(tot_occupations.mayor)
        sim.engine.occupation_types.add(tot_occupations.molder)
        sim.engine.occupation_types.add(tot_occupations.mortician)
        sim.engine.occupation_types.add(tot_occupations.nurse)
        sim.engine.occupation_types.add(tot_occupations.optometrist)
        sim.engine.occupation_types.add(tot_occupations.owner)
        sim.engine.occupation_types.add(tot_occupations.painter)
        sim.engine.occupation_types.add(tot_occupations.pharmacist)
        sim.engine.occupation_types.add(tot_occupations.plasterer)
        sim.engine.occupation_types.add(tot_occupations.plastic_surgeon)
        sim.engine.occupation_types.add(tot_occupations.plumber)
        sim.engine.occupation_types.add(tot_occupations.police_chief)
        sim.engine.occupation_types.add(tot_occupations.police_officer)
        sim.engine.occupation_types.add(tot_occupations.principal)
        sim.engine.occupation_types.add(tot_occupations.professor)
        sim.engine.occupation_types.add(tot_occupations.proprietor)
        sim.engine.occupation_types.add(tot_occupations.puddler)
        sim.engine.occupation_types.add(tot_occupations.quarry_man)
        sim.engine.occupation_types.add(tot_occupations.realtor)
        sim.engine.occupation_types.add(tot_occupations.seamstress)
        sim.engine.occupation_types.add(tot_occupations.secretary)
        sim.engine.occupation_types.add(tot_occupations.stocker)
        sim.engine.occupation_types.add(tot_occupations.shoemaker)
        sim.engine.occupation_types.add(tot_occupations.stonecutter)
        sim.engine.occupation_types.add(tot_occupations.tailor)
        sim.engine.occupation_types.add(tot_occupations.tattoo_artist)
        sim.engine.occupation_types.add(tot_occupations.taxi_driver)
        sim.engine.occupation_types.add(tot_occupations.teacher)
        sim.engine.occupation_types.add(tot_occupations.turner)
        sim.engine.occupation_types.add(tot_occupations.waiter)
        sim.engine.occupation_types.add(tot_occupations.whitewasher)
        sim.engine.occupation_types.add(tot_occupations.woodworker)

        # Register Business Archetypes
        sim.engine.business_archetypes.add("Bakery", tot_businesses.bakery)
        sim.engine.business_archetypes.add("Bank", tot_businesses.bank)
        sim.engine.business_archetypes.add("Bar", tot_businesses.bar)
        sim.engine.business_archetypes.add("BarberShop", tot_businesses.barbershop)
        sim.engine.business_archetypes.add("BusDepot", tot_businesses.bus_depot)
        sim.engine.business_archetypes.add(
            "CarpentryCompany", tot_businesses.carpentry_company
        )
        sim.engine.business_archetypes.add("Cemetery", tot_businesses.cemetery)
        sim.engine.business_archetypes.add("CityHall", tot_businesses.city_hall)
        sim.engine.business_archetypes.add(
            "ClothingStore", tot_businesses.clothing_store
        )
        sim.engine.business_archetypes.add("CoalMine", tot_businesses.coal_mine)
        sim.engine.business_archetypes.add(
            "ConstructionFirm", tot_businesses.construction_firm
        )
        sim.engine.business_archetypes.add("Dairy", tot_businesses.dairy)
        sim.engine.business_archetypes.add("DayCare", tot_businesses.day_care)
        sim.engine.business_archetypes.add("Deli", tot_businesses.deli)
        sim.engine.business_archetypes.add(
            "DentistOffice", tot_businesses.dentist_office
        )
        sim.engine.business_archetypes.add(
            "DepartmentStore", tot_businesses.department_store
        )
        sim.engine.business_archetypes.add("Dinner", tot_businesses.diner)
        sim.engine.business_archetypes.add("Distillery", tot_businesses.distillery)
        sim.engine.business_archetypes.add("DrugStore", tot_businesses.drug_store)
        sim.engine.business_archetypes.add("Farm", tot_businesses.farm)
        sim.engine.business_archetypes.add("FireStation", tot_businesses.fire_station)
        sim.engine.business_archetypes.add("Foundry", tot_businesses.foundry)
        sim.engine.business_archetypes.add(
            "FurnitureStore", tot_businesses.furniture_store
        )
        sim.engine.business_archetypes.add("GeneralStore", tot_businesses.general_store)
        sim.engine.business_archetypes.add("GroceryStore", tot_businesses.grocery_store)
        sim.engine.business_archetypes.add(
            "HardwareStore", tot_businesses.hardware_store
        )
        sim.engine.business_archetypes.add("Hospital", tot_businesses.hospital)
        sim.engine.business_archetypes.add("Hotel", tot_businesses.hotel)
        sim.engine.business_archetypes.add("Inn", tot_businesses.inn)
        sim.engine.business_archetypes.add(
            "InsuranceCompany", tot_businesses.insurance_company
        )
        sim.engine.business_archetypes.add("JewelryShop", tot_businesses.jewelry_shop)
        sim.engine.business_archetypes.add("LawFirm", tot_businesses.law_firm)
        sim.engine.business_archetypes.add(
            "OptometryClinic", tot_businesses.optometry_clinic
        )
        sim.engine.business_archetypes.add(
            "PaintingCompany", tot_businesses.painting_company
        )
        sim.engine.business_archetypes.add("Park", tot_businesses.park)
        sim.engine.business_archetypes.add("Pharmacy", tot_businesses.pharmacy)
        sim.engine.business_archetypes.add(
            "PlasticSurgeryClinic", tot_businesses.plastic_surgery_clinic
        )
        sim.engine.business_archetypes.add(
            "PlumbingCompany", tot_businesses.plumbing_company
        )
        sim.engine.business_archetypes.add(
            "PoliceStation", tot_businesses.police_station
        )
        sim.engine.business_archetypes.add("Quarry", tot_businesses.quarry)
        sim.engine.business_archetypes.add("RealtyFirm", tot_businesses.realty_firm)
        sim.engine.business_archetypes.add("Restaurant", tot_businesses.restaurant)
        sim.engine.business_archetypes.add("School", tot_businesses.school)
        sim.engine.business_archetypes.add(
            "ShoemakerShop", tot_businesses.shoemaker_shop
        )
        sim.engine.business_archetypes.add("SuperMarket", tot_businesses.supermarket)
        sim.engine.business_archetypes.add("TailorShop", tot_businesses.tailor_shop)
        sim.engine.business_archetypes.add("TattooParlor", tot_businesses.tattoo_parlor)
        sim.engine.business_archetypes.add("Tavern", tot_businesses.tavern)
        sim.engine.business_archetypes.add("TaxiDepot", tot_businesses.taxi_depot)


def get_plugin() -> Plugin:
    return TalkOfTheTownPlugin()
