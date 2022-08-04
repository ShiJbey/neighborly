import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from neighborly.core.business import OccupationDefinition
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.residence import ResidenceArchetypeLibrary, ResidenceArchetype
from neighborly.loaders import YamlDataLoader
from neighborly.plugins.default_plugin.activity import Activity, register_activity
from neighborly.plugins.default_plugin.businesses import (
    bartender_type,
    cashier_type,
    cook_type,
    dj_type,
    manager_type,
    owner_type,
    proprietor_type,
    sales_associate_type,
    security_type,
)
from neighborly.simulation import Plugin, Simulation

logger = logging.getLogger(__name__)

_RESOURCES_DIR = Path(os.path.abspath(__file__)).parent / "data"


@YamlDataLoader.section_loader("Activities")
def _load_activity_data(engine: NeighborlyEngine, data: List[Dict[str, Any]]) -> None:
    """Process data related to defining activities"""
    for entry in data:
        register_activity(Activity(entry["name"], trait_names=entry["traits"]))


class DefaultNameDataPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        self.initialize_tracery_name_factory(sim.get_engine())

    def initialize_tracery_name_factory(self, engine: NeighborlyEngine) -> None:
        # Load character name data
        engine.name_generator.load_names(
            rule_name="family_name", filepath=_RESOURCES_DIR / "names" / "surnames.txt"
        )
        engine.name_generator.load_names(
            rule_name="first_name",
            filepath=_RESOURCES_DIR / "names" / "neutral_names.txt",
        )
        engine.name_generator.load_names(
            rule_name="feminine_first_name",
            filepath=_RESOURCES_DIR / "names" / "feminine_names.txt",
        )
        engine.name_generator.load_names(
            rule_name="masculine_first_name",
            filepath=_RESOURCES_DIR / "names" / "masculine_names.txt",
        )

        # Load potential names for different structures in the town
        engine.name_generator.load_names(
            rule_name="restaurant_name",
            filepath=_RESOURCES_DIR / "names" / "restaurant_names.txt",
        )
        engine.name_generator.load_names(
            rule_name="bar_name", filepath=_RESOURCES_DIR / "names" / "bar_names.txt"
        )

        # Load potential names for the town
        engine.name_generator.load_names(
            rule_name="town_name",
            filepath=_RESOURCES_DIR / "names" / "US_settlement_names.txt",
        )


class DefaultBusinessesPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        # BusinessArchetype.register(restaurant_type)
        # BusinessArchetype.register(bar_type)
        # BusinessArchetype.register(department_store_type)
        #
        OccupationDefinition.register_type(manager_type)
        OccupationDefinition.register_type(sales_associate_type)
        OccupationDefinition.register_type(cashier_type)
        OccupationDefinition.register_type(dj_type)
        OccupationDefinition.register_type(bartender_type)
        OccupationDefinition.register_type(security_type)
        OccupationDefinition.register_type(cook_type)
        OccupationDefinition.register_type(owner_type)
        OccupationDefinition.register_type(proprietor_type)
        OccupationDefinition.register_type(OccupationDefinition(name="Server"))
        OccupationDefinition.register_type(OccupationDefinition(name="Host"))

        # sim.get_engine().add_business_archetype(
        #     EntityArchetype("Department Store")
        #     .add(
        #         Business,
        #         business_type="Department Store",
        #         hours="MTWRF 9:00-17:00, SU 10:00-15:00",
        #         owner_type="Owner",
        #         employees={
        #             "Cashier": 1,
        #             "Sales Associate": 2,
        #             "Manager": 1,
        #         },
        #     )
        #     .add(Location),
        #     min_population=25,
        #     max_instances=2,
        #     spawn_multiplier=2,
        # )


class DefaultResidencesPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        ResidenceArchetypeLibrary.register(ResidenceArchetype(name="House"))


class DefaultPlugin(Plugin):

    def setup(self, sim: Simulation, **kwargs) -> None:
        pass
        # LifeEventProcessor.register_event(DeathEvent())
        # LifeEventProcessor.register_event(StartedDatingEvent())
        # LifeEventProcessor.register_event(DatingBreakUpEvent())
        # LifeEventProcessor.register_event(UnemploymentEvent())
        # LifeEventProcessor.register_event(BecameBusinessOwnerEvent())
        # Load additional data from yaml
        # YamlDataLoader(filepath=_RESOURCES_DIR / "data.yaml").load(ctx.engine)
